# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import re
import sys
import datetime
import logging

# -----------------
# Third Party imports
# -------------------

from pubsub import pub
import anyio

#--------------
# local imports
# -------------

from zptess import __version__, REF, TEST
from zptess.main import arg_parser, configure_logging

class Deduplicater:
    '''Removes duplicates readings in TESS JSON payloads'''

    def __init__(self, role, log):
        self._role     = role
        self.log       = log
        self._prev_seq = None

    def write(self, data):
        cur_seq = data.get('udp', None)
        if cur_seq is not None and cur_seq != self._prev_seq:
            self._prev_seq = cur_seq
            pub.sendMessage('phot_sample', role=self._role, sample=data)
        elif cur_seq is None:
            pub.sendMessage('phot_sample', role=self._role, sample=data) # old protocol, not JSON protocol



class PhotometerService:

    NAME = "Photometer Service"

    def __init__(self, options, isRef):
        self.log = logging.getLogger(__name__)
        self.options = options
        self.isRef   = isRef  # Flag, is this instance for the reference photometer
        if isRef: 
            self.role = 'ref'
            self.label = REF.lower()
            self.msgspace = REF.upper()
        else:
            self.role = 'test'
            self.label = TEST.lower()
        proto, addr, port = chop(self.options['endpoint'], sep=':')
        self.factory   = self.buildFactory(options['old_proto'], proto)
           
  
    async def start(self):
        '''
        Starts the photometer service listens to a TESS
        Although it is technically a synchronous operation, it works well
        with inline callbacks
        '''
        self.log.info("Starting %s", self.name)
        self.protocol  = None
        self.info      = None # Photometer info
        self.deduplicater = Deduplicater(self.role, self.log)
        pub.subscribe(self.onUpdateZeroPoint, 'calib_flash_zp')
        # Async part form here ...
        try:
            self.info = None
            await self.connect()
            self.info = await self.getPhotometerInfo()
        except Exception as e:
            self.log.error("%s", e)
            pub.sendMessage('phot_offline', role=self.role)
        if self.info is None:
            pub.sendMessage('phot_offline', role=self.role)
        pub.sendMessage('phot_info', role=self.role, info=self.info)



    async def stop(self):
        self.log.info("Stopping %s", self.name)
        if self.protocol:
            self.protocol.stopProducing()
            if self.protocol.transport:
                self.log.info("Closing transport %s", self.options['endpoint'])
                self.protocol.transport.loseConnection()
            self.protocol = None
            pub.unsubscribe(self.onUpdateZeroPoint, 'calib_flash_zp')
        return super().stopService() # se we can handle the 'running' attribute
            
    # --------------
    # Photometer API 
    # --------------

    async def on_update_zero_point(self, zero_point):
        if not self.isRef:
            await self.save_zero_point(zero_point)


    async def save_zero_point_(self, zero_point):
        '''Writes Zero Point to the device.'''
        self.log.info("[%s] Updating ZP : %0.2f", self.label, zero_point)
        try:
            await self.protocol.writeZeroPoint(zero_point)
        except Exception as e:
            self.log.error("%s",e)
        else:
            self.log.info("[%s] Updated ZP : %0.2f", self.label, zero_point)

    # --------------
    # Helper methods
    # ---------------

    def connect(self):
        proto, addr, port = chop(self.options['endpoint'], sep=':')
        if proto == 'serial':
            protocol = self.factory.buildProtocol(addr)
            serport  = SerialPort(protocol, addr, reactor, baudrate=int(port))
            self.gotProtocol(protocol)
            self.log.info("Using serial port {tty} at {baud} bps", tty=addr, baud=port)
        elif proto == 'tcp':
            self.factory.tcp_deferred = defer.Deferred()
            self.factory.tcp_deferred.addTimeout(2, reactor)
            conn = reactor.connectTCP(addr, int(port), self.factory)
            protocol = yield self.factory.tcp_deferred
            self.gotProtocol(protocol)
            self.log.info("Connected to TCP endpoint {endpoint}", endpoint=self.options['endpoint'])
        else:
            protocol = self.factory.buildProtocol(addr)
            reactor.listenUDP(int(port), protocol)
            self.gotProtocol(protocol)
            self.log.info("listening on UCP endpoint {endpoint}", endpoint=self.options['endpoint'])


    async def getPhotometerInfo(self):
        info = await self.protocol.getPhotometerInfo()
        info['model'] = self.options['model']
        info['sensor'] = self.options['sensor']
        info['label'] = self.label
        info['role']  = self.role
        return info

    
    def get_protocol(self, old_payload, proto):
        if self.options['model'] == TESSW:
            import zptess.photometer.protocol.tessw
            factory = zptess.photometer.protocol.tessw.TESSProtocolFactory(
                model       = TESSW,
                log         = self.log,
                namespace   = self.msgspace, 
                role        = self.role, 
                config_dao  = self.options['config_dao'],  
                old_payload = old_payload, 
                transport_method = proto, 
            )
        elif self.options['model'] == TESSP:
            import zptess.photometer.protocol.tessp
            factory = zptess.photometer.protocol.tessp.TESSProtocolFactory(
                model     = TESSP, 
                log       = self.log,
                namespace = self.msgspace,
            )
        else:
            import zptess.photometer.protocol.tas
            factory = zptess.photometer.protocol.tas.TESSProtocolFactory(
                model     = TAS, 
                log       = self.log,
                namespace = self.msgspace,
            )
        return factory


    def gotProtocol(self, protocol):
        self.log.debug("got protocol")
        self.deduplicater.registerProducer(protocol, True)
        self.protocol  = protocol

# ====
# TEST
# ====

async def async_main():
    
    from zptess.photometer.protocol.transport import UDPTransport
    from zptess.photometer.protocol.photinfo import HTMLInfo

    parser = arg_parser(
        name = __name__,
        version = __version__,
        description = "Example UDP read I/O"
    )
    args = parser.parse_args(sys.argv[1:])
    configure_logging(args)
    logging.info("Preparing to listen to UDP")
    transport = UDPTransport()
    photinfo = HTMLInfo('test', '192.168.4.1')
    async with anyio.create_task_group() as tg:
        tg.start_soon(transport.readings)
        tg.start_soon(photinfo.get_info)


def main():
    anyio.run(async_main)