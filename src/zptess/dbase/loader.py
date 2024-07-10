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
import csv
import logging
import argparse
import asyncio
import datetime

# -------------------
# Third party imports
# -------------------


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionClass
from sqlalchemy.ext.asyncio import async_sessionmaker

from lica.sqlalchemy.asyncio.dbase import engine, AsyncSession
from lica.asyncio.photometer import Model as PhotModel, Role, Sensor
from lica.textual.logging import configure_log
from lica.textual.argparse import args_parser
from lica.validators import vfile, vdir

#--------------
# local imports
# -------------

from .. import __version__
from .model import Config, Round, Photometer, Sample, Summary, Batch

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS-W Zero Database Migration tool"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# -------------------
# Auxiliary functions
# -------------------

async def load_batch(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading batch data from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    row['email_sent'] = True if row['email_sent'] == '1' else False
                    row['begin_tstamp'] = datetime.datetime.strptime(row['begin_tstamp'], "%Y-%m-%dT%H:%M:%S") if row['begin_tstamp'] else None
                    row['end_tstamp'] = datetime.datetime.strptime(row['end_tstamp'], "%Y-%m-%dT%H:%M:%S") if row['end_tstamp'] else None
                    session.add(Batch(**row))

async def load_rounds(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading rounds from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    log.info("To be continued")


async def load_config(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading config from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    session.add(Config(**row))


async def load_photometer(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading photometer from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    row['sensor'] = None if not row['sensor'] else row['sensor']
                    row['firmware'] = None if not row['firmware'] else row['firmware']
                    row['filter'] = None if not row['filter'] else row['filter']
                    row['collector'] = None if not row['collector'] else row['collector']
                    phot = Photometer(**row)
                    session.add(phot)
                    
                   
            


async def load_summary(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading summary from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    mac = row['mac']; name = row['name']
                    del row['mac']; del row['name']
                    row['session'] = datetime.datetime.strptime(row['session'], "%Y-%m-%dT%H:%M:%S")
                    row['upd_flag'] = True if row['upd_flag'] == '1' else False
                    for key in ('zero_point','freq', 'zero_point_method', 'freq_method', 'mag', 'nrounds', 'prev_zp'):
                        row[key] = None if not row[key] else row[key]
                    q = select(Photometer).where(Photometer.mac==mac, Photometer.name==name)
                    summary = Summary(**row)
                    phot = (await session.scalars(q)).one_or_none()
                    if phot is not None:
                        summary.photometer = phot
                    else:
                        log.warn("photometer mot found by name %s, mac %s")
                    session.add(summary)

# --------------
# main functions
# --------------

TABLE = {
    'config': load_config,
    'batch': load_batch,
    'photometer': load_photometer,
    'summary': load_summary,
    'rounds': load_rounds,
}

async def loader(args) -> None:
    async with engine.begin() as conn:
        if args.command != 'all':
            func = TABLE[args.command]
            path = os.path.join(args.input_dir, args.command + '.csv')
            await func(path, AsyncSession)
        else:
            for name in ('config','batch'):
                path = os.path.join(args.input_dir, name + '.csv')
                func = TABLE[name]
                await func(path, AsyncSession)
    await engine.dispose()


def add_args(parser):

    subparser = parser.add_subparsers(dest='command')

    parser_config = subparser.add_parser('config', help='Load config CSV')
    parser_batch = subparser.add_parser('batch', help='Load config CSV')
    parser_phot = subparser.add_parser('photometer', help='Load photometer CSV')
    parser_summary = subparser.add_parser('summary', help='Load summary CSV')
    parser_rounds = subparser.add_parser('rounds', help='Load rounds CSV')
    parser_all = subparser.add_parser('all', help='Load all CSVs')

    parser_config.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV file')
    parser_batch.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV file')
    parser_phot.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV file')
    parser_summary.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV file')
    parser_rounds.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV file')
    parser_all.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory')

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
