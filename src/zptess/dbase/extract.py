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

from lica.textual.logging import configure_log
from lica.textual.argparse import args_parser
from lica.validators import vfile, vdir
from lica.sqlite import open_database

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

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------

def write_csv(path: str, header, iterable, delimiter: str =';'):
    with open(path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter)
        writer.writerow(header)
        for row in iterable:
            writer.writerow(row)


def extract_batch(path: str, conn) -> None:
    log.info("Extracting from batch_t table.")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT begin_tstamp, end_tstamp, calibrations, email_sent, comment 
        FROM batch_t 
        ORDER BY begin_tstamp
    ''')
    write_csv(path, BATCH_H, cursor)


def extract_config(path: str, conn) -> None:
    log.info("Extracting from config_t table.")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT section, property AS prop, value
        FROM config_t 
        ORDER BY section, prop
    ''')
    write_csv(path, CONFIG_H, cursor)


def extract_photometer(path: str, conn) -> None:
    log.info("Extracting from summary_t table for photometer data.")
    cursor = conn.cursor()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT name,mac,sensor,model,firmware,filter,plug,box,collector
        FROM summary_t
        ORDER BY name
    ''')
    write_csv(path, PHOTOMETER_H, cursor)
 

def extract_summary(path: str, conn) -> None:
    log.info("Extracting from summary_t table for summary calibration data.")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT name,mac,session,role,calibration,calversion,author,nrounds,offset AS zp_offset,
            upd_flag,prev_zp,zero_point,zero_point_method,freq,freq_method,mag,comment
        FROM summary_t
        ORDER BY name
    ''')
    write_csv(path, SUMMARY_H, cursor)


def extract_rounds(path: str, conn) -> None:
    log.info("Extracting from rounds_t table.")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT session,round,role,begin_tstamp,end_tstamp,central,freq,stddev,mag,zp_fict,zero_point,nsamples,duration
        FROM rounds_t
        ORDER BY session, round, role
    ''')
    write_csv(path, ROUNDS_H, cursor)



def extract_samples(path: str, conn) -> None:
    log.info("Extracting from samples_t table.")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT session,tstamp,role,seq,freq,temp_box 
        FROM samples_t 
        ORDER BY session, tstamp, role 
    ''')
    write_csv(path, SAMPLES_H, cursor)


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
    connection, _ = open_database(env_var='SOURCE_DATABASE')
    if args.command not in ('all',):
        func = TABLE[args.command]
        path = os.path.join(args.input_dir, args.command + '.csv')
        func(path, connection)
        log.info("done.")
    else:
        for name in ('config','batch', 'photometer', 'summary', 'rounds', 'samples'):
            path = os.path.join(args.input_dir, name + '.csv')
            func = TABLE[name]
            func(path, connection)
    connection.close()


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
    extract(args)

if __name__ == '__main__':
    main()
