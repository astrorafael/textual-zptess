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
from zptess.utils.misc import chop

# ----------------
# Module constants
# ----------------


# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# ----------------
# Module functions
# ----------------



# ----------
# Exceptions
# ----------


# -------
# Classes
# -------



class TESSProtocolFactory:

    def build(self, role, old_payload):
        device_url = decouple.config('REF_ENDPOINT') if role == 'ref' else  decouple.config('TEST_ENDPOINT')
        log.info(device_url)
        transport, name, number = chop(device_url,sep=':')
        number = int(number) if number else 80
        if transport == 'serial' and role == 'ref':
            photinfo_obj = DBaseInfo(role)
        else:
            photinfo_obj = HTMLInfo(role, addr=name)
        if transport == 'udp':
            transport_obj = UDPTransport(port=number)
        elif transport == 'tcp':
            transport_obj = TCPTransport(host=name, port=number)
        else:
            transport_obj = SerialTransport(port=name, baudrate=number)
        payload_obj = OldPayload(role) if old_payload else JSONPayload(role)
        return transport_obj, photinfo_obj, payload_obj
       
 
__all__ = [
    "TESSProtocolFactory",
]
