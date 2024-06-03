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

from zptess import __version__
from zptess.utils.argsparse import args_parser
from zptess.utils.logging import configure
from zptess.tui.main import ZpTessApp
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

async def bootstrap():
    app = ZpTessApp()
    async with anyio.create_task_group() as tg:
        log.info("Creating the TUI task")
        tg.start_soon(app.run_async)


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
