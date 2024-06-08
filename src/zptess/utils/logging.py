# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import logging
import logging.handlers

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------


def configure(args):
    '''Configure the root logger'''
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    # set the root logger level
    log = logging.getLogger()
    log.setLevel(level)
    # Log formatter
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)-4s] %(message)s')
    # create console handler and set level to debug
    if args.console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.DEBUG)
        log.addHandler(ch)
    elif args.textual:
        import textual.logging
        ch = textual.logging.TextualHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.DEBUG)
        log.addHandler(ch)
    # Create a file handler suitable for logrotate usage
    if args.log_file:
        # fh = logging.handlers.WatchedFileHandler(args.log_file)
        fh = logging.handlers.TimedRotatingFileHandler(args.log_file, when='midnight', interval=1, backupCount=365)
        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG)
        log.addHandler(fh)
