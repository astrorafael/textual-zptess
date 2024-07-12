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
import math
import logging
import argparse
import asyncio
import datetime
import statistics

from typing import List

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
from .model import Round, Photometer, Sample, Summary
from .. import CentralTendency

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS-W Browser tool"

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split('.')[-1])

# ------------------
# Auxiliar functions
# ------------------

def central(method):
    f = statistics.mode
    if method == CentralTendency.MEAN:
        f = statistics.mean
    elif method == CentralTendency.MEDIAN:
        f = statistics.median
    return f

# -----------------
# Auxiliary classes
# -----------------

class DbgPhotometer(Photometer):
    pass

class DbgSummary(Summary):

    async def check(self):
        rounds = await self.awaitable_attrs.rounds
        N = len(rounds)
        assert self.nrounds is None or self.nrounds == N, "self.rounds != len(rounds)"
        if self.nrounds is not None:
            freq_method = central(self.freq_method)
            result = freq_method([r.freq for r in rounds])
            f = self.freq
            assert math.fabs(result - f) < 0.001, f"{self} => computed f={result:.2f}, stored f={f:.2f}"
            if self.role == Role.TEST:
                zp_method = central(self.zero_point_method)
                zp_set = [r.zero_point for r in rounds]
                zp_final = zp_method(zp_set) + self.zp_offset
                log.info("ZP(%s)%s +  OFFSET (%s) = RESULT (%s)", 
                    self.zero_point_method, zp_set, self.zp_offset, zp_final, )
                zp_stored = self.zero_point
                assert math.fabs(zp_final - zp_stored) <= 0.011, f"{self} => computed zp={zp_final:.2f}, stored zp={zp_stored:.2f}"
        log.info("self check ok: %s", self)


class DbgRound(Round):
    
    async def check(self):
        samples = sorted(await self.awaitable_attrs.samples)
        N = len(samples)
        assert self.nsamples == N, "self.nsamples != len(samples)"
        assert self.begin_tstamp is None or self.begin_tstamp == samples[0].tstamp, "Begin round timestamp mismatch"
        assert self.end_tstamp   is None or self.end_tstamp  == samples[-1].tstamp, "End round timestamp mismatch"
        freq_method = central(self.central)
        for s in samples:
            assert s.role == self.role, f"Round role {self.role} = Sample role {s.role}"
        freqs = [s.freq for s in samples]
        freq = freq_method(freqs)
        assert self.freq == freq, f"Round Freq = {self.freq}, Samples {self.central} {freq}"
        log.info("self check ok: %s", self)


class DbgSample(Sample):
    pass

# -------------------
# Auxiliary functions
# -------------------       

async def get_all_sessions(async_session: async_sessionmaker[AsyncSessionClass]) -> List[datetime.datetime]:
    async with async_session() as session:
        async with session.begin():
            q = select(DbgSummary.session).order_by(DbgSummary.role.asc())
            return (await session.scalars(q)).all()

async def browse_summary(meas_session, check, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    if meas_session is not None:
        await browse_summary_single(meas_session, check, async_session)
    else:
        meas_session = await get_all_sessions(async_session)
        for ses in meas_session:
            await browse_summary(ses, check, async_session)

async def browse_rounds(meas_session, check, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    if meas_session is not None:
        await browse_rounds_single(meas_session, check, async_session)
    else:
        meas_session = await get_all_sessions(async_session)
        for ses in meas_session:
            await browse_rounds_single(ses, check, async_session)

async def browse_all(meas_session, check, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    if meas_session is not None:
        await browse_all_single(meas_session, check, async_session)
    else:
        meas_session = await get_all_sessions(async_session)
        for ses in meas_session:
            await browse_all_single(ses, check, async_session)


async def browse_summary_single(meas_session, check, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            log.info("browsing summary for %s", meas_session)
            q = (select(DbgPhotometer, DbgSummary).
                join(DbgSummary).
                where(DbgSummary.session == meas_session).
                order_by(DbgSummary.role.asc())
            )
            result = (await session.execute(q)).all()
            for row in result:
                phot = row[0]
                summ = row[1]
                log.info("name=%-10s, mac=%s, role=%-4s, calib=%s nrounds=%s, zp=%s (%s), freq=%s (%s)", 
                    phot.name, phot.mac, 
                    summ.role, summ.calibration, summ.nrounds, summ.zero_point, summ.zero_point_method, summ.freq, summ.freq_method)
                if check:
                    await summ.check()

async def browse_rounds_single(meas_session, check, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            log.info("browsing rounds for %s", meas_session)
            q = (select(DbgPhotometer, DbgSummary, DbgRound).
                join(DbgSummary, DbgPhotometer.id == DbgSummary.phot_id).
                join(DbgRound, DbgSummary.id == DbgRound.summ_id).
                filter(DbgSummary.session == meas_session).
                order_by(DbgSummary.role.asc())
            )
            result = (await session.execute(q)).all()
            log.info("Found %d round results", len(result))
            for row in result:
                phot = row[0]
                summary = row[-2]
                round_ = row[-1]
                assert summary.role == round_.role, f"Summary role {summary.role} = Round role {round_.role}"
                if check:
                    await round_.check()
            
               

async def browse_all_single(meas_session, check, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    await browse_summary_single(meas_session, check, async_session)
    await browse_rounds_single(meas_session, check, async_session)
            

            

# --------------
# main functions
# --------------

TABLE = {
    'summary': browse_summary,
    'rounds': browse_rounds,
    'all': browse_all,
}

async def browser(args) -> None:
    async with engine.begin() as conn:
        if args.command != 'all':
            func = TABLE[args.command]
            meas_session = args.session
            await func(meas_session, args.check, AsyncSession)
        else:
            for name in ('summary', 'rounds', 'samples'):
                meas_session = args.session
                func = TABLE[name]
                await func(meas_session, args.check, AsyncSession)
    await engine.dispose()


def add_args(parser):

    subparser = parser.add_subparsers(dest='command')
    
    parser_summary = subparser.add_parser('summary', help='Browse summary data')
    parser_rounds = subparser.add_parser('rounds', help='Browse rounds data')
    parser_samples = subparser.add_parser('samples', help='Browse samples data')
    parser_all = subparser.add_parser('all', help='Browse all data')

    parser_summary.add_argument('-s', '--session', metavar='<YYYY-MM-DDTHH:MM:SS>', type=vdate, default=None, help='Session date')
    parser_summary.add_argument('-c', '--check',  action='store_true',  default=False, help='Consistency check between summary and rounds')
   
    parser_rounds.add_argument('-s', '--session', type=vdate, default=None, help='Session date')
    parser_rounds.add_argument('-c', '--check',  action='store_true',  default=False, help='Consistency check between rounds and samples')
   
    parser_samples.add_argument('-s', '--session', type=vdate, default=None, help='Session date')
    parser_samples.add_argument('-c', '--check',  action='store_true',  default=False, help='Consistency check?')
    
    parser_all.add_argument('-s', '--session', type=vdate, default=None, help='Session date')
    parser_all.add_argument('-c', '--check',  action='store_true',  default=False, help='Consistency check?')


   
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
