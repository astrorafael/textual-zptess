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
        self.quit_event =  None

    def set_view(self, view):
        self.view = view

    async def wait(self):
        self.quit_event = anyio.Event() if self.quit_event is None else self.quit_event
        await self.quit_event.wait()
        raise  KeyboardInterrupt("User quits")

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

    async def run_async(self, role):
        async with anyio.create_task_group() as tg:
            if role == 'ref':
                self.ref_cs = tg.cancel_scope
                tg.start_soon(self.ref_photometer.readings)
                tg.start_soon(self.receptor, 'ref', self.receive_stream1)
            else:
                 with anyio.CancelScope() as cs:
                    self.test_cs = cs
                    tg.start_soon(self.test_photometer.readings)
                    tg.start_soon(self.receptor, 'test', self.receive_stream2)
                   