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
from pubsub import pub

#--------------
# local imports
# -------------


from zptess import __version__
from zptess.main import arg_parser, configure_logging

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__)

# -------------------
# Auxiliary functions
# -------------------

class UDPTransport:

	def __init__(self, host='0.0.0.0', port=2255):
		self.local_host = host
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


class SerialTransport:
	pass


