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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from lica.textual.argparse import args_parser
from lica.textual.logging import configure_log
from lica.textual.logging import configure_log

from lica.sqlalchemy.asyncio.dbase import url, engine, Model, AsyncSession


#--------------
# local imports
# -------------

from .. import __version__
from .model import Config, Sample

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

async def populate(async_session: async_sessionmaker[AsyncSession]) -> None:
    async with async_session() as session:
        async with session.begin():
            session.add(Config(section="database", prop="uuid", value=str(uuid.uuid4())))
            session.add(Config(section="calibration", prop="author", value="Rafael González"))
            session.add(Config(section="calibration", prop="samples", value=5))
            session.add(Config(section="calibration", prop="wavelength", value=350))


            for i in range(0,16):
                Sample()
    


async def schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)
        await populate(AsyncSession)
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
    log.info("Creating/Opening schema %s", url)
    asyncio.run(schema())


if __name__ == '__main__':
    main()