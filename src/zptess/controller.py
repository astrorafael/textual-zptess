# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import sys
import argparse
import logging

# -------------------
# Third party imports
# -------------------

import anyio

#--------------
# local imports
# -------------

from zptess import TEST
from zptess.photometer.tessw import Photometer

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

class Controller:

    def __init__(self, tui):
        self.tui = tui

        self.send_stream1, self.receive_stream1 = anyio.create_memory_object_stream[dict](max_buffer_size=4)
        self.ref_photometer = Photometer(role='ref', old_payload=True, stream=self.send_stream1)

        self.send_stream2, self.receive_stream2 = anyio.create_memory_object_stream[dict](max_buffer_size=4)
        self.test_photometer =  Photometer(role='test', old_payload=False, stream=self.send_stream2)
       
        

    async def run_async(self):

        logging.info("Obtaining Photometers info")
        info = await self.ref_photometer.get_info()
        logging.info(info)
        info = await self.test_photometer.get_info()
        logging.info(info)

        logging.info("Preparing to listen to photometers") 

        # Catching exception groups this way is pre-Python 3.11
        with catch({
            ValueError: handle_error,
            KeyError: handle_error,
            #anyio.BrokenResourceError: handle_error,
        }):
            async with anyio.create_task_group() as tg:
                tg.start_soon(ref_photometer.readings)
                tg.start_soon(test_photometer.readings)
                tg.start_soon(receptor, 'ref', receive_stream1)
                tg.start_soon(receptor, 'test', receive_stream2)
