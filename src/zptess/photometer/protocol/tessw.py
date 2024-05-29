# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import logging
import datetime

#--------------------
# Third Party imports
# -------------------

import decouple

#--------------
# local imports
# -------------

from zptess.photometer.protocol.transport import UDPTransport, TCPTransport, SerialTransport
from zptess.photometer.protocol.payload   import JSONPayload, OldPayload
from zptess.photometer.protocol.photinfo  import HTMLInfo, DBaseInfo
from zptess.utils.misc import chop, label

# ----------------
# Module constants
# ----------------


# -----------------------
# Module global variables
# -----------------------


# ----------------
# Module functions
# ----------------



# ----------
# Exceptions
# ----------


# -------
# Classes
# -------



class Photometer:

    def __init__(self, role, old_payload, stream):
        self.role = role
        self.label = label(role)
        self.log = logging.getLogger(self.label)
        self.decoder = OldPayload(self) if old_payload else JSONPayload(self)
        self.stream = stream
        device_url = decouple.config('REF_ENDPOINT') if role == 'ref' else  decouple.config('TEST_ENDPOINT')
        transport, name, number = chop(device_url,sep=':')
        number = int(number) if number else 80
        if transport == 'serial' and role == 'ref':
            self.info = DBaseInfo(self)
        else:
            self.info = HTMLInfo(self, addr=name)
        if transport == 'udp':
            self.transport = UDPTransport(self, port=number)
        elif transport == 'tcp':
            self.transport = TCPTransport(self, host=name, port=number)
        else:
            self.transport = SerialTransport(self, port=name, baudrate=number)
        
    # -----------
    # Private API
    # -----------

    async def handle_readings(self, payload, timestamp):
        flag, message = self.decoder.decode(payload, timestamp)
        if flag:
            await self.stream.send((payload,timestamp))


    # ----------
    # Public API
    # ----------

    async def readings(self):
        async with self.stream:
            return await self.transport.readings()

    async def get_info(self, timeout=5):
        return await self.info.get_info(timeout)

    async def save_zero_point(self, zero_point):
        return await self.info.save_zero_point(zero_point)

 
__all__ = [
    "TESSProtocolFactory",
]
