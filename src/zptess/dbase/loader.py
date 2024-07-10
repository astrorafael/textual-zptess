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
                    batch = Batch(**row)
                    log.info("%r", batch)
                    session.add(batch)


async def load_config(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading config from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    config = Config(**row)
                    log.info("%r", config)
                    session.add(config)


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
                    log.info("%r", phot)
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
                    row['calibration'] = None if not row['calibration'] else row['calibration']
                    for key in ('zero_point', 'zp_offset','prev_zp','freq','mag'):
                        row[key] = float(row[key]) if row[key] else None
                    for key in ('zero_point_method', 'freq_method', 'nrounds'):
                        row[key] = None if not row[key] else row[key]
                    q = select(Photometer).where(Photometer.mac==mac, Photometer.name==name)
                    summary = Summary(**row)
                    phot = (await session.scalars(q)).one()
                    summary.photometer = phot
                    log.info("%r", summary)
                    session.add(summary)


async def load_rounds(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading rounds from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    row['seq'] = row['round']
                    del row['round']
                    row['session'] = datetime.datetime.strptime(row['session'], "%Y-%m-%dT%H:%M:%S")
                    row['begin_tstamp'] = datetime.datetime.strptime(row['begin_tstamp'], "%Y-%m-%dT%H:%M:%S.%f") if row['begin_tstamp'] else None
                    row['end_tstamp'] = datetime.datetime.strptime(row['end_tstamp'], "%Y-%m-%dT%H:%M:%S.%f") if row['end_tstamp'] else None
                    for key in ('freq', 'stddev','mag','zp_fict','zero_point','duration'):
                        row[key] = float(row[key]) if row[key] else None
                    round_ = Round(**row)
                    log.info("%r", round_)
                    session.add(round_)


async def _new_sample(session, row, role, meas_session):
    q = (select(Summary.phot_id).
        where(Summary.session == meas_session).
        where(Summary.role == role))
    phot_id = (await session.scalars(q)).one_or_none()
    if not phot_id:
        log.warn("No sample for %s because no photometer for session = %s, role %s", row, meas_session, role)
        return None   
    row['phot_id'] = phot_id 
    return Sample(**row)


async def _link_sample_to_rounds(session, sample, meas_session):
    q = (select(Round).
        where(Round.session == meas_session).
        where(Round.role == sample.role))
    rounds = (await session.scalars(q)).all()
    for r in rounds:
        if r.begin_tstamp <= sample.tstamp <= r.end_tstamp:
            sample.rounds.append(r) # no need to do r.append(sample) !!!


async def load_samples(path, async_session: async_sessionmaker[AsyncSessionClass]) -> None:
     async with async_session() as session:
        async with session.begin():
            log.info("loading samples from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    meas_session = datetime.datetime.strptime(row['session'], "%Y-%m-%dT%H:%M:%S")
                    del row['session']
                    role = Role.REF if row['role'] == 'ref' else Role.TEST
                    row['tstamp'] = datetime.datetime.strptime(row['tstamp'], "%Y-%m-%dT%H:%M:%S.%f")
                    row['temp_box'] = float(row['temp_box']) if row['temp_box'] else None
                    row['freq'] = float(row['freq'])
                    row['seq'] = int(row['seq']) if row['seq'] else None
                    sample = await _new_sample(session, row, role, meas_session)
                    if not sample:
                        continue
                    await _link_sample_to_rounds(session, sample, meas_session)
                    log.info("%r", sample)
                    session.add(sample)
# --------------
# main functions
# --------------

TABLE = {
    'config': load_config,
    'batch': load_batch,
    'photometer': load_photometer,
    'summary': load_summary,
    'rounds': load_rounds,
    'samples': load_samples,
}

async def loader(args) -> None:
    async with engine.begin() as conn:
        if args.command != 'all':
            func = TABLE[args.command]
            path = os.path.join(args.input_dir, args.command + '.csv')
            await func(path, AsyncSession)
        else:
            for name in ('config','batch', 'photometer', 'summary', 'rounds', 'samples'):
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
    parser_samples = subparser.add_parser('samples', help='Load samples CSV')
    parser_all = subparser.add_parser('all', help='Load all CSVs')

    parser_config.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_batch.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_phot.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_summary.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_rounds.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_samples.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_all.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')

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
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    asyncio.run(loader(args))

if __name__ == '__main__':
    main()
