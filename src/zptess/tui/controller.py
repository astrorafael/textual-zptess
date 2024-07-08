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

from lica.misc import measurements_session_id
from lica.asyncio.photometer import Role, Model
from lica.asyncio.photometer.builder import PhotometerBuilder
from lica.sqlalchemy.asyncio.dbase import engine

#--------------
# local imports
# -------------

from ..ring import RingBuffer 

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

# -------
# Classes
# -------

class Controller:

    def __init__(self, ring_buffer_size=75):
        self.photometer = [None, None]
        self.producer = [None, None]
        self.consumer = [None, None]
        self.ring = [None, None]
        self.cur_mac = [None, None]

        builder = PhotometerBuilder(engine) # For the reference photometer using database info

        self.photometer[Role.TEST] = builder.build(Model.TESSW, Role.TEST)
        self.photometer[Role.REF] =  builder.build(Model.TESSW, Role.REF)

        self.ring[Role.REF] = RingBuffer(ring_buffer_size)
        self.ring[Role.TEST] = RingBuffer(ring_buffer_size)
        self.quit_event =  None

    # ----------------------------------------
    # Public API to be used by the Textual TUI
    # ----------------------------------------

    def set_view(self, view):
        self.view = view

    def quit(self):
        self.view.exit(return_code=2)


    async def load(self):
        '''Load configuration data from the database'''
        log.info("loading configuration data")
        async with self.Session() as session:
            q = select(Config.value).where(Config.section == 'calibration', Config.prop == 'samples')
            self._samples = int((await session.scalars(q)).one_or_none())
          
    async def get_info(self, role):
        '''Get Photometer Info'''
        log = logging.getLogger(str(role))
        try:
            info = await self.photometer[role].get_info()
        except asyncio.exceptions.TimeoutError:
            line = f"Failed contacting {str(role)} photometer"
            log.error(line)
            self.view.append_log(role, line)
            self.view.reset_switch(role)
        except Exception as e:
            log.error(e)
        else:
            self.view.clear_metadata_table(role)
            self.view.update_metadata_table(role, info)
            async with self.Session() as session:
                session.begin()
                try:
                    q = select(DbPhotometer).where(DbPhotometer.mac == info.get('mac'))
                    dbphot = (await session.scalars(q)).one_or_none()
                    if not dbphot:
                        session.add(
                            DbPhotometer(
                                name= info.get('name'), 
                                mac = info.get('mac'),
                                sensor = info.get('sensor'),
                                model = info.get('model'),
                                firmware = info.get('firmware'),
                                zero_point = info.get('zp'),
                                freq_offset = info.get('freq_offset'),
                            )
                        )
                    await session.commit()
                except Exception as e:
                    log.warn("Ignoring already saved photometer entry")
                    await session.rollback()
            self.cur_mac[role] = info.get('mac')

    async def receive(self, role):
        while True:
            msg = await self.photometer[role].queue.get()
            self.ring[role].append(msg)
            line = f"{msg['tstamp'].strftime('%Y-%m-%d %H:%M:%S')} [{msg.get('seq')}] f={msg['freq']} Hz, tbox={msg['tamb']}, tsky={msg['tsky']}"
            self.view.append_log(role, line)
            self.view.update_progress(role, 1)
            data = self.ring[role].frequencies()
            self.view.update_graph(role, data)

    def cancel_readings(self, role):
        self.producer[role].cancel()
        self.consumer[role].cancel()
        self.view.append_log(role, "READINGS PAUSED")

    def start_readings(self, role):
        self.photometer[role].clear()
        self.consumer[role] = asyncio.create_task(self.receive(role))
        self.producer[role] = asyncio.create_task(self.photometer[role].readings())
       