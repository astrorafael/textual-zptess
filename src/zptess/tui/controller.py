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
import asyncio

# -------------------
# Third party imports
# -------------------


#--------------
# local imports
# -------------

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

    def __init__(self):
        self.ref_photometer = Photometer(role='ref', old_payload=True)
        self.tst_photometer =  Photometer(role='test', old_payload=False)
        self.quit_event =  None

    def set_view(self, view):
        self.view = view

    async def wait(self):
        self.quit_event = asyncio.Event() if self.quit_event is None else self.quit_event
        await self.quit_event.wait()
        raise  KeyboardInterrupt("User quits")

    async def receptor(self, role, photometer, queue):
        try:
            info = await photometer.get_info()
            self.view.clear_metadata(role)
            self.view.update_metadata(role, info)
        except Exception as e:
            log.error(e)
        else:
            while True:
                widget = self.view.get_log_widget(role)
                msg = await queue.get()
                message = f"{msg['tstamp'].strftime('%Y-%m-%d %H:%M:%S')} [{msg.get('udp')}] f={msg['freq']} Hz, tbox={msg['tamb']}"
                widget.write_line(message)
           
    def cancel_readings(self, role):
        if role == 'ref':
            self.ref_task.cancel()
            self.ref_reader.cancel()
        else:
            self.tst_task.cancel()
            self.tst_task.cancel()
        widget = self.view.get_log_widget(role)
        widget.write_line("READINGS PAUSED")

    def start_readings(self, role):
        if role == 'ref':
            photometer = self.ref_photometer
            queue = photometer.queue
            self.ref_reader = asyncio.create_task(self.receptor(role, photometer, queue))
            self.ref_task = asyncio.create_task(photometer.readings())
        else:
            photometer = self.tst_photometer
            queue = photometer.queue
            self.tst_reader = asyncio.create_task(self.receptor(role, photometer, queue))
            self.tst_task = asyncio.create_task(photometer.readings())
                   