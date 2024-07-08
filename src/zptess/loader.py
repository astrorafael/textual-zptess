# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import csv
import logging
import argparse
import asyncio

# -------------------
# Third party imports
# -------------------

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from lica.sqlalchemy.asyncio.dbase import engine, AsyncSession
from lica.asyncio.photometer import Model as PhotModel, Role, Sensor
from lica.textual.logging import configure_log
from lica.textual.argparse import args_parser
from lica.validators import vfile

#--------------
# local imports
# -------------

from zptess import __version__
from zptess.dbase.model import Config, Round, Photometer, Sample

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS-W Zero Point Calibration tool"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# -------------------
# Auxiliary functions
# -------------------

async def load_photometer(path, async_session: async_sessionmaker[AsyncSession]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading photometer from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    row['mac'] = None if not row['mac'] else row['mac']
                    row['sensor'] = None if not row['sensor'] else row['sensor']
                    row['firmware'] = None if not row['firmware'] else row['firmware']
                    row['filter'] = None if not row['filter'] else row['filter']
                    row['collector'] = None if not row['collector'] else row['collector']
                    if row['mac']:
                        phot = Photometer(**row)
                        session.add(phot)
                    else:
                        log.warn("NO MAC FOR %s", row)
                   
            


async def load_summary(path, async_session: async_sessionmaker[AsyncSession]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading summary from %s", path)


# --------------
# main functions
# --------------

async def loader(args) -> None:
    async with engine.begin() as conn:
        if args.command == 'photometer':
            await load_photometer(args.input_file, AsyncSession)
        elif  args.command == 'summary':
            await load_summary(args.input_file, AsyncSession)
    await engine.dispose()


def add_args(parser):

    subparser = parser.add_subparsers(dest='command')

    parser_phot = subparser.add_parser('photometer', help='Load photometer CSV')
    parser_summary = subparser.add_parser('summary', help='Load summary CSV')

    
    parser_phot.add_argument('-i', '--input-file', type=vfile, required=True, help='Input CSV file')
    parser_summary.add_argument('-i', '--input-file', type=vfile, required=True, help='Input CSV file')

def main():
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = DESCRIPTION
    )
    add_args(parser)
    args = parser.parse_args(sys.argv[1:])
    configure_log(args)
    asyncio.run(loader(args))

if __name__ == '__main__':
    main()
