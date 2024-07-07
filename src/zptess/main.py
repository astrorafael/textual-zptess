# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import logging

# -------------------
# Third party imports
# -------------------


from lica.sqlalchemy.asyncio.dbase import engine, AsyncSession
from lica.textual.argparse import args_parser
from lica.textual.logging import configure_log

#--------------
# local imports
# -------------

from . import __version__

from .tui.application import MyTextualApp
from .tui.controller import Controller

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS-W Zero Point Calibration tool"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()

# -------------------
# Auxiliary functions
# -------------------

def main():
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = DESCRIPTION
    )
    args = parser.parse_args(sys.argv[1:])
    configure_log(args)
    try:
        controller = Controller()
        tui = MyTextualApp(controller, DESCRIPTION)
        controller.set_view(tui)
        tui.run()
    except KeyboardInterrupt:
        log.warn("Application quits by user request")
