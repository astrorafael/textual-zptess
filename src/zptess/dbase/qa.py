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

DESCRIPTION = "TESS-W Calibration Database Quality Assurance tool"

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

def magnitude(zp, freq):
    return zp - 2.5*math.log10(freq)

# -----------------
# Auxiliary classes
# -----------------

class DbgPhotometer(Photometer):
    pass

class DbgSummary(Summary):

    def assert_nrounds(self, rounds):
        N = len(rounds)
        assert self.nrounds is None or self.nrounds == N, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Summary computed #rounds= {N}, stored #rounds = {self.nrounds})"

    def assert_freq_from_rounds(self, rounds):
        freqs = [r.freq for r in rounds]
        mags = [magnitude(r.zp_fict, r.freq) for r in rounds]
        central_func = central(self.freq_method)
        freq = central_func(freqs)
        assert math.fabs(freq - self.freq) < 0.0005, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Summary computed f={freq:.2f}, stored f={self.freq:.2f}"
        return freq

    def assert_mag_from_rounds(self, rounds, freq):
        mag = magnitude(rounds[0].zp_fict, freq)
        assert math.fabs(mag - self.mag) < 0.005, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Summary computed mag={mag:.2f} from computed freq {freq}, stored mag={self.mag:.2f}"
        mags =  [magnitude(r.zp_fict, r.freq) for r in rounds]
        central_func = central(self.freq_method)
        mag = central_func(mags)
        assert math.fabs(mag - self.mag) < 0.005, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Summary computed mag={mag:.2f}, stored mag={self.mag:.2f}"
        
    def assert_zp_from_rounds(self, rounds):
        zps = [r.zero_point for r in rounds]
        central_func = central(self.zero_point_method)
        zp = central_func(zps) + self.zp_offset
        assert math.fabs(zp - self.zero_point) < 0.005, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Summary computed zp={zp:.2f}, stored zp={self.zero_point:.2f}"


    async def check(self, photometer):
        self.n = photometer.name
        self.m = photometer.mac
        self.s = self.session
        rounds = await self.awaitable_attrs.rounds
        self.assert_nrounds(rounds)
        if self.nrounds is not None:
            freq = self.assert_freq_from_rounds(rounds)
            self.assert_mag_from_rounds(rounds, freq)
            if self.role == Role.TEST:
                self.assert_zp_from_rounds(rounds)
        log.info("[%s] [%s] [%s] Summary self check ok", self.n, self.m, self.s)


class DbgRound(Round):

    def assert_round_magnitude(self) -> float:
        mag = self.zp_fict - 2.5*math.log10(self.freq)
        assert math.fabs(self.mag - mag) < 0.005, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Round #{self.seq} computed mag = {mag} @ zp = {self.zp_fict}, stored mag {self.mag}"

    def assert_freq_from_samples(self, samples) -> float:
        '''Computes the central frequnency from its samples'''
        freqs = [s.freq for s in samples]
        central_func = central(self.central)
        freq = central_func(freqs)
        assert math.fabs(self.freq - freq) < 0.0005, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Round #{self.seq} stored f = {self.freq}, computed f = {freq} [{self.central}]"
        stddev = statistics.stdev(freqs, freq)
        assert math.fabs(self.stddev - stddev) < 0.005, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Round #{self.seq} stored \u03C3 f = {self.stddev}, computed \u03C3 f = {stddev} Hz ({self.central})"

    def assert_no_timestamps(self):
        assert self.begin_tstamp is None and self.end_tstamp is None, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Round #{self.seq} Expected empty timestamp windows, got beg={self.begin_tstamp} end={self.end_tstamp}"

    def assert_samples(self, samples):
        N = len(samples)
        assert self.nsamples == N, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Round #{self.seq} stored NS = {self.nsamples},  computed NS={N}"
        assert self.begin_tstamp == samples[0].tstamp, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Round #{self.seq} Begin round timestamp mismatch"
        assert self.end_tstamp  == samples[-1].tstamp, \
            f"[{self.n}] [{self.m}] [{self.s!s}] Round #{self.seq} End round timestamp mismatch"
        for s in samples:
            assert s.role == self.role, \
                f"[{self.n}] [{self.m}] [{self.s!s}] Round #role {self.role} = Sample role {s.role}"
        return samples

    async def check(self,photometer, summary):
        self.n = photometer.name
        self.m = photometer.mac
        self.s = summary.session
        self.assert_round_magnitude()  
        total_samples = await summary.awaitable_attrs.samples
        if self.nsamples > 0 and len(total_samples) == 0:
            self.assert_no_timestamps()
            log.warn("[%s] [%s] [%s] Round #%d self check ok. NO SAMPLES, (%d) reported.",
              self.n, self.m, self.s, self.seq, self.nsamples)
            return
        samples = sorted(await self.awaitable_attrs.samples)
        self.assert_samples(samples)
        self.assert_freq_from_samples(samples)
        log.info("[%s] [%s] [%s] Round #%d self check ok", self.n, self.m, self.s, self.seq)


class DbgSample(Sample):

    async def check(self, photometer, summary):
        n = photometer.name
        m = photometer.mac
        s = summary.session
        rounds = await self.awaitable_attrs.rounds
        rseqs = [r.seq for r in rounds]
        log.info("[%s] [%s] [%s] Sample #%d in Rounds %s. self check ok", n, m, s, self.id, rseqs)


# -------------------
# Auxiliary functions
# -------------------       

async def get_all_sessions(async_session: async_sessionmaker[AsyncSessionClass]) -> List[datetime.datetime]:
    async with async_session() as session:
        async with session.begin():
            q = select(DbgSummary.session).order_by(DbgSummary.role.asc())
            return (await session.scalars(q)).all()

async def check_summary(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    if meas_session is not None:
        await check_summary_single(meas_session, async_session)
    else:
        meas_session = await get_all_sessions(async_session)
        for ses in meas_session:
            await check_summary(ses, async_session)

async def check_rounds(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    if meas_session is not None:
        await check_rounds_single(meas_session, async_session)
    else:
        meas_session = await get_all_sessions(async_session)
        for ses in meas_session:
            await check_rounds_single(ses, async_session)

async def check_samples(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    if meas_session is not None:
        await check_samples_single(meas_session, async_session)
    else:
        meas_session = await get_all_sessions(async_session)
        for ses in meas_session:
            await check_samples_single(ses, async_session)

async def check_all(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    if meas_session is not None:
        await check_all_single(meas_session, async_session)
    else:
        meas_session = await get_all_sessions(async_session)
        for ses in meas_session:
            await check_all_single(ses, async_session)


async def check_summary_single(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            q = (select(DbgPhotometer, DbgSummary).
                join(DbgSummary).
                where(DbgSummary.session == meas_session).
                order_by(DbgSummary.role.asc())
            )
            result = (await session.execute(q)).all()
            for row in result:
                photometer = row[0]
                summary = row[1]
                await summary.check(photometer)

async def check_rounds_single(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            q = (select(DbgPhotometer, DbgSummary, DbgRound).
                join(DbgSummary, DbgPhotometer.id == DbgSummary.phot_id).
                join(DbgRound, DbgSummary.id == DbgRound.summ_id).
                filter(DbgSummary.session == meas_session).
                order_by(DbgSummary.role.asc())
            )
            result = (await session.execute(q)).all()
            for row in result:
                photometer = row[0]
                summary = row[-2]
                round_ = row[-1]
                await round_.check(photometer, summary)
            
async def check_samples_single(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            q = (select(DbgPhotometer, DbgSummary, DbgSample).
                join(DbgSummary, DbgPhotometer.id == DbgSummary.phot_id).
                join(DbgSample, DbgSummary.id == DbgSample.summ_id).
                filter(DbgSummary.session == meas_session).
                order_by(DbgSummary.role.asc())
            )
            result = (await session.execute(q)).all()
            for row in result:
                photometer = row[0]
                summary = row[-2]
                sample = row[-1]
                await sample.check(photometer, summary)


async def check_all_single(meas_session, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    await check_summary_single(meas_session, async_session)
    await check_rounds_single(meas_session, async_session)
    await check_samples_single(meas_session, async_session)
            

            

# --------------
# main functions
# --------------

TABLE = {
    'summary': check_summary,
    'rounds': check_rounds,
    'samples': check_samples,
    'all': check_all,
}

async def qa(args) -> None:
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

    parser_summary.add_argument('-s', '--session', metavar='<YYYY-MM-DDTHH:MM:SS>', type=vdate, default=None, help='Session date')
    parser_rounds.add_argument('-s', '--session', type=vdate, default=None, help='Session date')
    parser_samples.add_argument('-s', '--session', type=vdate, default=None, help='Session date')
    parser_all.add_argument('-s', '--session', type=vdate, default=None, help='Session date')
 


   
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
    asyncio.run(qa(args))

if __name__ == '__main__':
    main()
