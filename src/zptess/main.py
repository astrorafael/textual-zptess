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
import logging.handlers

# -------------------
# Third party imports
# -------------------

import anyio
from exceptiongroup import catch, ExceptionGroup

#--------------
# local imports
# -------------

from zptess import __version__
from zptess.utils.argsparse import args_parser
from zptess.utils.logging import configure
from zptess.tui.application import ZpTessApp
from zptess.tui.controller import Controller

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

async def bootstrap():
    with catch({
        ValueError: handle_error,
        KeyError: handle_error,
        KeyboardInterrupt: handle_error
        #anyio.BrokenResourceError: handle_error,
    }):
        controller = Controller()
        tui = ZpTessApp(controller)
        controller.set_view(tui)
        async with anyio.create_task_group() as tg:
            tg.start_soon(tui.run_async)
            tg.start_soon(controller.wait)
           

def main():
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = "Example Textual App"
    )
   
    args = parser.parse_args(sys.argv[1:])
    configure(args)
    anyio.run(bootstrap)
