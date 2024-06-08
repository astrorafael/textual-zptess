# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import re
import sys
import datetime
import logging
import asyncio

# ---------------------
# Third party libraries
# ---------------------

import datetime

import asyncstdlib as a
from exceptiongroup import catch, ExceptionGroup

from zptess import __version__
from zptess.photometer import label, REF, TEST
from zptess.utils.argsparse import args_parser
from zptess.utils.logging import configure
from zptess.photometer.tessw import Photometer



def handle_error(excgroup: ExceptionGroup) -> None:
    for exc in excgroup.exceptions:
        logging.error(exc)

async def async_main():

    ref_photometer = Photometer(role=REF, old_payload=True)
    ref_queue = ref_photometer.get_queue()

    tst_photometer = Photometer(role=TEST, old_payload=False)
    tst_queue = tst_photometer.get_queue()
   
    logging.info("Obtaining Photometers info")
    info = await ref_photometer.get_info()
    logging.info(info)
    logging.info("Preparing to listen to photometers")

    loop = asyncio.get_running_loop()
    t1 = loop.create_task(ref_photometer.readings())
    t2 = loop.create_task(receptor(REF, ref_queue))
    t3 = loop.create_task(tst_photometer.readings())
    t4 = loop.create_task(receptor(TEST, tst_queue))
    await asyncio.gather(t1, t2)


async def receptor(role, queue):
    log = logging.getLogger(label(role))
    i = 0
    while True:
        message = await queue.get()
        i += 1
        log.info("{%02d} %s", i, message)



def main():
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = "Example Photometer Build"
    )
    args = parser.parse_args(sys.argv[1:])
    configure(args)
    log = logging.getLogger()
    try:
        asyncio.run(async_main())
    except asyncio.exceptions.CancelledError:
        log.error("Cancelled at user's request")