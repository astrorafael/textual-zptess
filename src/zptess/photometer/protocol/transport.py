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

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# -------------------
# Auxiliary functions
# -------------------

class UDPTransport:

    def __init__(self, parent, port=2255, task_status = anyio.TASK_STATUS_IGNORED):
        self.parent = parent
        self.log = parent.log
        self.local_host = '0.0.0.0'
        self.local_port = port
        self.task_status = task_status

    async def readings(self):
        '''This is meant to be a task'''
        async with await anyio.create_udp_socket(
            family = socket.AF_INET, 
            local_host = self.local_host,
            local_port = self.local_port
        ) as udp:
            self.task_status.started()
            async for payload, (host, port) in udp:
                now = datetime.datetime.now(datetime.timezone.utc)
                await self.parent.handle_readings(payload, now)


class TCPTransport:

    def __init__(self, parent, host="192.168.4.1", port=23, task_status = anyio.TASK_STATUS_IGNORED):
        self.parent = parent
        self.log = parent.log
        self.host = host
        self.port = port
        self.task_status = task_status

    async def readings(self):
        '''This is meant to be a task'''
        async with await anyio.connect_tcp(
            remote_host = self.host, 
            remote_port = self.port 
        ) as tcp:
            self.task_status.started()
            async for payload in tcp:
                now = datetime.datetime.now(datetime.timezone.utc)
                await self.parent.handle_readings(payload, now)


class SerialTransport:
    
    def __init__(self, parent, port="/dev/ttyUSB0", baudrate=9600, task_status = anyio.TASK_STATUS_IGNORED):
        self.parent = parent
        self.log = parent.log
        self.baudrate = baudrate
        self.port = port
        self.task_status = task_status

    async def readings(self):
        '''This is meant to be a task'''
        async with anyio_serial.Serial(
            port = self.port, 
            baudrate = self.baudrate
        ) as serial_port:
            self.task_status.started()
            while True:
                payload = await serial_port.receive_until(delimiter=b'\r\n', max_bytes = 4096)
                now = datetime.datetime.now(datetime.timezone.utc)
                if len(payload):
                    await self.parent.handle_readings(payload, now)

                    