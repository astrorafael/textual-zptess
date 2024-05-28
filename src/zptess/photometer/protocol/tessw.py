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
from zptess.photometer.protocol.photinfo  import HTMLInfo


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

    def __init__(self, model, role, old_payload=False):
        self._model = model
        self._role = role
        self._old_payload = old_payload

    def build(self):
        device_url = decouple.config('REF_ENDPOINT') if self._role == 'ref' else  decouple.config('TEST_ENDPOINT')
        transport, name, number = chop(device_url)
        number = int(number) if number else 80
        if transport == 'serial' and self.role == 'ref':
            photinfo_obj = DBaseInfo(self._role)
        else:
            photinfo_obj = HTMLInfo(self._role, addr=name)
        if transport == 'udp':
            transport_obj = UDPTransport(host=name, port=number)
        elif transport == 'tcp':
            transport_obj = TCPTransport(host=name, port=number)
        else:
            transport_obj = SerialTransport(port=name, baudrate=number)
        payload_obj = OldPayload(self._role) if self._old_payload else JSONPayload(self._role)
        return transport_obj, photinfo_obj, payload_obj
       
 
__all__ = [
    "TESSProtocolFactory",
]
