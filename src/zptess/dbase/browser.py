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


from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionClass
from sqlalchemy.ext.asyncio import async_sessionmaker

from lica.sqlalchemy.asyncio.dbase import engine, AsyncSession
from lica.asyncio.photometer import Model as PhotModel, Role, Sensor
from lica.textual.logging import configure_log
from lica.textual.argparse import args_parser
from lica.validators import vfile, vdir, vdate

#--------------
# local imports
# -------------

from .. import __version__
from .model import Config, Round, Photometer, Sample, Summary, Batch, SamplesRounds

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS-W Browser tool"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------       

async def browse_summary(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            log.info("browsing summary for %s", meas_session)
            q = (select( Photometer.name, Photometer.mac, Summary.role, Summary.calibration, Summary.nrounds, Summary.zero_point).
                join(Photometer).
                where(Summary.session == meas_session).
                order_by(Summary.role.asc())
                )
            result = (await session.execute(q)).all()
            for row in result:
                log.info(row)
            


async def browse_rounds(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            log.info("browsing rounds for %s", meas_session)
            q = (select(Photometer.name, Photometer.mac, Summary.role, Summary.calibration, Summary.nrounds, Summary.zero_point, Round.seq).
                join(Photometer).
                join(Round).
                where(Summary.session == meas_session).
                order_by(Summary.role.asc())
                )
            result = (await session.execute(q)).all()
            for row in result:
                log.info(row)
            


async def browse_samples(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            log.info("browsing samples for %s", meas_session)
            q = (select(Photometer.name, Photometer.mac, Summary, Round).
                join(Photometer).
                join(Round).
                where(Summary.session == meas_session).
                order_by(Summary.role.asc())
            )
            result = (await session.execute(q)).all()
            for row in result:
                log.info(row)
                round_ = row[-1]
                samples = await round_.awaitable_attrs.samples
                for sample in samples:
                    log.info(sample)


            

            

# --------------
# main functions
# --------------

TABLE = {
    'summary': browse_summary,
    'rounds': browse_rounds,
    'samples': browse_samples,
}

async def browser(args) -> None:
    async with engine.begin() as conn:
        if args.command != 'all':
            func = TABLE[args.command]
            meas_session = args.session
            await func(meas_session, AsyncSession)
        else:
            for name in ('summary', 'rounds', 'samples'):
                meas_session = args.session
                func = TABLE[name]
                await func(meas_session, AsyncSession)
    await engine.dispose()


def add_args(parser):

    subparser = parser.add_subparsers(dest='command')
    
    parser_summary = subparser.add_parser('summary', help='Browse summary data')
    parser_rounds = subparser.add_parser('rounds', help='Browse rounds data')
    parser_samples = subparser.add_parser('samples', help='Browse samples data')
    parser_all = subparser.add_parser('all', help='Browse all data')

    parser_summary.add_argument('-s', '--session', metavar='<YYYY-MM-DDTHH:MM:SS>', type=vdate, required = True, help='Session date')
    parser_rounds.add_argument('-s', '--session', type=vdate, required = True, help='Session date')
    parser_samples.add_argument('-s', '--session', type=vdate, required = True, help='Session date')
    parser_all.add_argument('-s', '--session', type=vdate, required = True, help='Session date')


   
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
    if args.verbose:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("aiosqlite").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    asyncio.run(browser(args))

if __name__ == '__main__':
    main()
