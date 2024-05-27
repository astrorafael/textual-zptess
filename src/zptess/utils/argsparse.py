# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import argparse

#--------------
# local imports
# -------------

from zptess import __version__

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# -------------------
# Auxiliary functions
# -------------------

def args_parser(name, version, description):
    # create the top-level parser
    parser = argparse.ArgumentParser(prog=name, description=description)
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, version))
    group0 = parser.add_mutually_exclusive_group()
    group0.add_argument('--console', action='store_true', help='Log to vanilla console.')
    group0.add_argument('--textual', action='store_true', help='Log to Textual development console.')
    parser.add_argument('--log-file', type=str, metavar="<FILE>", default=None, help='Log to file.')
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--verbose', action='store_true', help='Verbose output.')
    group1.add_argument('--quiet',   action='store_true', help='Quiet output.')
    return parser
