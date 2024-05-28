# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------
import socket
import logging
import datetime

# -----------------
# Third Party imports
# -------------------

import anyio
import anyio_serial

from pubsub import pub

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -------------------
# Auxiliary functions
# -------------------

class UDPTransport:

    def __init__(self, port=2255):
        self.local_host = '0.0.0.0'
        self.local_port = port

    async def readings(self):
        async with await anyio.create_udp_socket(
            family = socket.AF_INET, 
            local_host = self.local_host,
            local_port = self.local_port
        ) as udp:
            async for payload, (host, port) in udp:
                now = datetime.datetime.now(datetime.timezone.utc)
                pub.sendMessage('reading', timestamp=now, payload=payload)
                log.info("%s => %s", now, payload)  


class TCPTransport:

    def __init__(self, host="192.168.4.1", port=23):
        self.host = host
        self.port = port

    async def readings(self):
        async with await anyio.connect_tcp(
            remote_host = self.host, 
            remote_port = self.port 
        ) as tcp:
            async for payload in tcp:
                now = datetime.datetime.now(datetime.timezone.utc)
                pub.sendMessage('reading', timestamp=now, payload=payload)
                log.info("%s => %s", now, payload)  


class SerialTransport:
    
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.baudrate = baudrate
        self.port = port

    async def readings(self):
        async with anyio_serial.Serial(
            port = self.port, 
            baudrate = self.baudrate
        ) as port:
            while True:
                payload = await port.receive_until(delimiter=b'\n', max_bytes = 4096):
                now = datetime.datetime.now(datetime.timezone.utc)
                pub.sendMessage('reading', timestamp=now, payload=payload)
                log.info("%s => %s", now, payload)