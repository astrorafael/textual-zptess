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

import asyncstdlib as a
import anyio
from exceptiongroup import catch, ExceptionGroup
from textual import work

#--------------
# local imports
# -------------

from zptess import TEST
from zptess.utils.misc import label
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


def handle_error(excgroup: ExceptionGroup) -> None:
    for exc in excgroup.exceptions:
        log.error(exc)

class Controller:

    def __init__(self):
        self.send_stream1, self.receive_stream1 = anyio.create_memory_object_stream[dict](max_buffer_size=4)
        self.ref_photometer = Photometer(role='ref', old_payload=True, stream=self.send_stream1)
        self.send_stream2, self.receive_stream2 = anyio.create_memory_object_stream[dict](max_buffer_size=4)
        self.test_photometer =  Photometer(role='test', old_payload=False, stream=self.send_stream2)

    def set_view(self, view):
        self.view = view

    async def receptor(self, role, stream):
        photometer = self.ref_photometer if role == 'ref' else  self.test_photometer
        try:
            info = await photometer.get_info()
            self.view.update_metadata(role, info)
        except Exception as e:
            log.error(e)
        else:
            widget = self.view.get_log_widget(role)
            async with stream:
                async for i, msg in a.enumerate(stream, start=1):
                    message = f"{msg['tstamp'].strftime('%Y-%m-%d %H:%M:%S')} [{msg.get('udp')}] f={msg['freq']} Hz, tbox={msg['tamb']}"
                    widget.write_line(message)

    async def run_async(self):
        self.view.quit_event = anyio.Event()
        # Catching exception groups this way is pre-Python 3.11
        with catch({
            ValueError: handle_error,
            KeyError: handle_error,
            KeyboardInterrupt: handle_error,
            #anyio.BrokenResourceError: handle_error,
        }):
            async with anyio.create_task_group() as tg:
                tg.start_soon(self.test_photometer.readings)
                tg.start_soon(self.ref_photometer.readings)
                tg.start_soon(self.receptor, 'test', self.receive_stream2)
                tg.start_soon(self.receptor, 'ref', self.receive_stream1)
                await self.view.quit_event.wait()
                raise  KeyboardInterrupt("User quits")
