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
import asyncio

# -----------------
# Third Party imports
# -------------------

import aioserial

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


class UDPTransport(asyncio.DatagramProtocol):

    def __init__(self, parent, port=2255):
        self.parent = parent
        self.log = parent.log
        self.local_host = '0.0.0.0'
        self.local_port = port

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, payload, addr):
        now = datetime.datetime.now(datetime.timezone.utc)
        self.parent.handle_readings(payload, now)

    def connection_lost(self, exc):
        if not  self.on_conn_lost.cancelled():
            self.on_conn_lost.set_result(True)

    async def readings(self):
        loop = asyncio.get_running_loop()
        self.on_conn_lost = loop.create_future()
        transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: self,
            local_addr=(self.local_host, self.local_port)
        )
        try:
            await self.on_conn_lost
        finally:
            self.transport.close()
        


class TCPTransport(asyncio.Protocol):

    def __init__(self, parent, host="192.168.4.1", port=23):
        self.parent = parent
        self.log = parent.log
        self.host = host
        self.port = port
        self.task_status = task_status

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        now = datetime.datetime.now(datetime.timezone.utc)
        self.parent.handle_readings(payload, now)

    def connection_lost(self, exc):
        if not  self.on_conn_lost.cancelled():
            self.on_conn_lost.set_result(True)

    async def readings(self):
        loop = asyncio.get_running_loop()
        self.on_conn_lost = loop.create_future()
        transport, self.protocol = await loop.create_connection(
            lambda: self,
            self.host, self.port
        )
        try:
            await self.on_conn_lost
        finally:
            self.transport.close()



class SerialTransport:
    
    def __init__(self, parent, port="/dev/ttyUSB0", baudrate=9600):
        self.parent = parent
        self.log = parent.log
        self.port = port
        self.baudrate = baudrate
        self.serial = None
 
    async def readings(self):
        '''This is meant to be a task'''
        self.serial = aioserial.AioSerial(port=self.port, baudrate=self.baudrate)
        while self.serial is not None:
            try:
                payload = await self.serial.readline_async()
                now = datetime.datetime.now(datetime.timezone.utc)
                payload = payload[:-2] # Strips \r\n
                if len(payload):
                    self.parent.handle_readings(payload, now)
            except:
                self.serial.close()
                self.serial = None

                    