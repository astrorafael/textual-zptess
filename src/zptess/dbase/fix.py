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
import datetime
import sqlite3
import statistics

# -------------------
# Third party imports
# -------------------

from lica.textual.logging import configure_log
from lica.textual.argparse import args_parser
from lica.sqlite import open_database
from lica.validators import vdate

#--------------
# local imports
# -------------

from .. import __version__
from .. import CentralTendency

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS-W Calibration Database fix stuff tool"

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__.split('.')[-1])

# -------------------
# Auxiliary functions
# -------------------

def central(method):
    f = statistics.mode
    if method == CentralTendency.MEAN:
        f = statistics.mean
    elif method == CentralTendency.MEDIAN:
        f = statistics.median
    return f


def get_rounds(conn, session, role):
    params = {'session': session, 'role': role}
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT begin_tstamp, end_tstamp, round, freq, central, stddev
        FROM rounds_t
        WHERE session = :session AND role = :role
        AND begin_tstamp IS NOT NULL AND end_tstamp IS NOT NULL
    ''', params)
    return cursor


def samples(conn, session, begin_tstamp, end_tstamp, role):
    params = {'session': session, 'role': role, 'begin_tstamp': begin_tstamp, 'end_tstamp': end_tstamp}
    cursor = conn.cursor()
    cursor.execute('''
        SELECT freq FROM samples_t
        WHERE session = :session AND role = :role
        AND tstamp BETWEEN :begin_tstamp AND :end_tstamp
    ''', params)
    return list(result[0] for result in cursor)


def fix_stddev(conn, new_stddev, old_stddev, name, mac, session, role, seq):
    params = {'session': session, 'role': role, 'seq': seq, 'new_stddev': new_stddev, 'old_stddev': old_stddev}
    with conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE rounds_t
            SET stddev = :new_stddev       
            WHERE session = :session AND role = :role AND round = :seq
            AND stddev = :old_stddev
        ''', params)
        log.info("[%s] [%s] [%s] Round #%d old %f => new %f", name, mac, session, seq, old_stddev, new_stddev)
       

def compare_and_fix_stddev(conn, name, mac, session, role, seq, freq, freqs, freq_method, stddev):
    central_func = central(freq_method)
    computed_freq = central_func(freqs)
    computed_stddev = statistics.stdev(freqs, computed_freq)
    if math.fabs(computed_stddev - stddev) > 0.005:
        log.warn("[%s] [%s] [%s] Round #%d computed \u03C3 %f, != stored \u03C3 %f, ", name, mac, session, seq, computed_stddev, stddev)
        computed2_stddev = statistics.stdev(freqs)
        if not math.fabs(computed2_stddev - stddev) < 0.005:
            log.error( f"[{name}] [{mac}] [{session}] Computed \u03C3 {computed_stddev} = Stored \u03C3 {stddev}")
        else:
            fix_stddev(conn, computed_stddev, stddev, name, mac, session, role, seq)
        #assert math.fabs(computed_stddev - stddev) < 0.005, f"[{name}] [{mac}] [{session}] Computed \u03C3 {computed_stddev} = Stored \u03C3 {stddev}"

def fix_rounds_stddev(conn, name, mac, session) -> None:
    for role in ('ref', 'test'):
        for begin_tstamp, end_tstsamp, seq, freq, central, stddev in get_rounds(conn, session, role):
            freqs = samples(conn, session, begin_tstamp, end_tstsamp, role)
            compare_and_fix_stddev(conn, name, mac, session, role, seq, freq, freqs, central, stddev)
  
    

def sessions(conn):
    log.info("Getting all sessions.")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT name, mac, session FROM summary_t ORDER BY session ASC
    ''')
    return cursor

# --------------
# main functions
# --------------

def fix(args) -> None:
    connection, _ = open_database(env_var='SOURCE_DATABASE')
    if args.stddev:
        if args.session:
            fix_rounds_stddev(connection, args.session)
        else:
            for name, mac, session in sessions(connection):
                fix_rounds_stddev(connection, name, mac, session)

    log.info("done.")
    connection.close()


def add_args(parser):
    subparser = parser.add_subparsers(dest='command')
    parser_rounds = subparser.add_parser('rounds', help='Fix rounds stuff')
    roex = parser_rounds.add_mutually_exclusive_group(required=True)
    roex.add_argument('-t','--stddev',  action='store_true',  help='Fix rounds stddev')
    parser_rounds.add_argument('-s', '--session', type=vdate, default=None, help='Session date')
    

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
    fix(args)

if __name__ == '__main__':
    main()
