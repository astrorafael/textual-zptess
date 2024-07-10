# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import uuid
import asyncio
import logging

from typing import Optional, List
from datetime import datetime

# ------------------
# SQLAlchemy imports
# -------------------

from lica.textual.argparse import args_parser
from lica.textual.logging import configure_log
from lica.sqlalchemy.asyncio.dbase import url, engine, Model

#--------------
# local imports
# -------------

from .. import __version__
# We must pull one model to make it work
from .model import Config

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# -------------------
# Auxiliary functions
# -------------------

async def schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)
    await engine.dispose()


def main():
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = "TESSDB initial Schema generation"
    )
    args = parser.parse_args(sys.argv[1:])
    configure_log(args)
    if args.verbose:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    log.info("Creating new schema for %s", url)
    asyncio.run(schema())

if __name__ == '__main__':
    main()
