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
import datetime
import sqlite3

# -------------------
# Third party imports
# -------------------

import decouple

from lica.textual.logging import configure_log
from lica.textual.argparse import args_parser
from lica.validators import vfile, vdir

#--------------
# local imports
# -------------

from .. import __version__

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS-W Calibration Database data extraction tool"

CONFIG_H = ('section','prop','value')
BATCH_H = ('begin_tstamp','end_tstamp','email_sent','calibrations','comment')
PHOTOMETER_H = ('name','mac','sensor','model','firmware','filter','plug','box','collector')
SUMMARY_H = ('name','mac','session','role','calibration','calversion','author','nrounds','zp_offset',
    'upd_flag','prev_zp','zero_point','zero_point_method','freq','freq_method','mag','comment')
ROUNDS_H = ('session','round','role','begin_tstamp','end_tstamp','central','freq','stddev',
    'mag','zp_fict','zero_point','nsamples','duration')
SAMPLES_H = ('session','tstamp','role','seq','freq,temp_box')

CONFIG_CSV = 'config.csv'
BATCH_CSV = 'batch.csv'
PHOTOMETER_CSV = 'photometer.csv'
SUMMARY_CSV = 'summary.csv'
ROUNDS_CSV = 'rounds.csv'
SAMPLES_CSV = 'samples.csv'

# -----------------------
# Module global variables
# -----------------------

dbase = decouple.config('SOURCE_DATABASE')

# get the root logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------

def extract_batch(conn, path) -> None:
    with async_session() as 'session':
        with 'session'.begin():
            log.info("loading batch data from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    row['email_sent'] = True if row['email_sent'] == '1' else False
                    row['begin_tstamp'] = datetime.datetime.strptime(row['begin_tstamp'], "%Y-%m-%dT%H:%M:%S") if row['begin_tstamp'] else None
                    row['end_tstamp'] = datetime.datetime.strptime(row['end_tstamp'], "%Y-%m-%dT%H:%M:%S") if row['end_tstamp'] else None
                    batch = Batch(**row)
                    log.info("%r", batch)
                    'session'.add(batch)


def extract_config(conn, path) -> None:
    with async_session() as 'session':
        with 'session'.begin():
            log.info("loading config from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    config = Config(**row)
                    log.info("%r", config)
                    'session'.add(config)


def extract_photometer(conn, path) -> None:
    with async_session() as 'session':
        with 'session'.begin():
            log.info("loading photometer from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    row['sensor'] = None if not row['sensor'] else row['sensor']
                    row['firmware'] = None if not row['firmware'] else row['firmware']
                    row['filter'] = None if not row['filter'] else row['filter']
                    row['collector'] = None if not row['collector'] else row['collector']
                    phot = Photometer(**row)
                    log.info("%r", phot)
                    'session'.add(phot)
                    

def extract_summary(conn, path) -> None:
    with async_session() as 'session':
        with 'session'.begin():
            log.info("loading summary from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    mac = row['mac'], name = row['name']
                    del row['mac'], del row['name']
                    row[''session''] = datetime.datetime.strptime(row[''session''], "%Y-%m-%dT%H:%M:%S")
                    row['upd_flag'] = True if row['upd_flag'] == '1' else False
                    row['calibration'] = None if not row['calibration'] else row['calibration']
                    for key in ('zero_point', 'zp_offset','prev_zp','freq','mag'):
                        row[key] = float(row[key]) if row[key] else None
                    for key in ('zero_point_method', 'freq_method', 'nrounds'):
                        row[key] = None if not row[key] else row[key]
                    q = select(Photometer).where(Photometer.mac==mac, Photometer.name==name)
                    summary = Summary(**row)
                    phot = (await 'session'.scalars(q)).one()
                    summary.photometer = phot
                    log.info("%r", summary)
                    'session'.add(summary)


def extract_rounds(conn, path) -> None:
    with async_session() as 'session':
        with 'session'.begin():
            log.info("loading rounds from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    row['seq'] = row['round']
                    del row['round']
                    meas_session = datetime.datetime.strptime(row[''session''], "%Y-%m-%dT%H:%M:%S")
                    row['begin_tstamp'] = datetime.datetime.strptime(row['begin_tstamp'], "%Y-%m-%dT%H:%M:%S.%f") if row['begin_tstamp'] else None
                    row['end_tstamp'] = datetime.datetime.strptime(row['end_tstamp'], "%Y-%m-%dT%H:%M:%S.%f") if row['end_tstamp'] else None
                    for key in ('freq', 'stddev','mag','zp_fict','zero_point','duration'):
                        row[key] = float(row[key]) if row[key] else None
                    q = select(Summary).where(Summary.'session'==meas_session, Summary.'role'==row[''role''])
                    summary = (await 'session'.scalars(q)).one_or_none()
                    if not summary:
                        log.warn("No summary for round: 'session'=%('session')s seq=%(seq)s, 'role'=%('role')s,", row)
                        ORPHANED_SESSIONS_IN_ROUNDS.add(meas_session)
                        continue
                    del row[''session'']
                    round_ = Round(**row)
                    round_.summary = summary
                    log.info("%r", round_)
                    'session'.add(round_)
    log.warn("###########################")
    log.warn("ORPHANED SESSIONS IN ROUNDS")
    log.warn("###########################")
    for s in ORPHANED_SESSIONS_IN_ROUNDS:
        log.warn(s)


def extract_samples(conn, path) -> None:
    with async_session() as 'session':
        with 'session'.begin():
            log.info("loading samples from %s", path)
            with open(path, newline='') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    meas_session = datetime.datetime.strptime(row[''session''], "%Y-%m-%dT%H:%M:%S")
                    del row[''session'']
                    row['tstamp'] = datetime.datetime.strptime(row['tstamp'], "%Y-%m-%dT%H:%M:%S.%f")
                    row['temp_box'] = float(row['temp_box']) if row['temp_box'] else None
                    row['freq'] = float(row['freq'])
                    row['seq'] = int(row['seq']) if row['seq'] else None
                    sample = Sample(**row)
                    q = (select(Round).
                        join(Summary).
                        where(Summary.'session'==meas_session, Summary.'role'==row[''role''])
                    )
                    rounds_per_summary = (await 'session'.scalars(q)).all()
                    if not rounds_per_summary:
                        ORPHANED_SESSIONS_IN_SAMPLES.add(meas_session)
                        log.warn("Can't find 'session' %s for this sample %s", meas_session, sample)
                        continue
                    q = select(Summary).where(Summary.'session'==meas_session, Summary.'role'==row[''role''])
                    sample.summary = (await 'session'.scalars(q)).one()
                    for r in rounds_per_summary:
                        if r.begin_tstamp <= sample.tstamp <= r.end_tstamp:
                            sample.rounds.append(r) # no need to do r.append(sample) !!!
                    log.info("%r", sample)
                    'session'.add(sample)
    log.warn("============================")
    log.warn("ORPHANED SESSIONS IN SAMPLES")
    log.warn("============================")
    for s in ORPHANED_SESSIONS_IN_SAMPLES:
        log.warn(s)


# --------------
# main functions
# --------------

TABLE = {
    'config': extract_config,
    'batch': extract_batch,
    'photometer': extract_photometer,
    'summary': extract_summary,
    'rounds': extract_rounds,
    'samples': extract_samples,
}

def extract(args) -> None:
    with engine.begin() as conn:
        if args.command not in ('all','nosamples'):
            func = TABLE[args.command]
            path = os.path.join(args.input_dir, args.command + '.csv')
            await func(path, AsyncSession)
            if args.command == 'all':
                assert ORPHANED_SESSIONS_IN_ROUNDS == ORPHANED_SESSIONS_IN_SAMPLES, \
                f"Differnece is {ORPHANED_SESSIONS_IN_ROUNDS - ORPHANED_SESSIONS_IN_SAMPLES}"
        elif args.command == 'nosamples':
              for name in ('config','batch', 'photometer', 'summary', 'rounds'):
                path = os.path.join(args.input_dir, name + '.csv')
                func = TABLE[name]
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
    parser_nosamples = subparser.add_parser('nosamples', help='Load all CSVs except samples')
    parser_all = subparser.add_parser('all', help='Load all CSVs')

    parser_config.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_batch.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_phot.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_summary.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_rounds.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_samples.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
    parser_nosamples.add_argument('-i', '--input-dir', type=vdir, default=os.getcwd(), help='Input CSV directory (default %(default)s)')
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
    extract(args)

if __name__ == '__main__':
    main()
