# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import json
import socket
import asyncio
import logging



# -----------------
# Third Party imports
# -------------------

import anyio

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
log = logging.getLogger()

# -------------------
# Auxiliary functions
# -------------------


async def readings():
    async with await anyio.create_udp_socket(
        family = socket.AF_INET, 
        local_host = "0.0.0.0",
        local_port = 2255
    ) as udp:
        async for packet, (host, port) in udp:
            log.info(json.loads(packet.decode()))
        



def main():
    parser = arg_parser(
        name = __name__,
        version = __version__,
        description = "Example UDP read I/O"
    )
    args = parser.parse_args(sys.argv[1:])
    configure_logging(args)
    logging.info("Preparing to listen to UDP")
    anyio.run(readings)