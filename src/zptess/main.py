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
import logging

# ---------------
# Textual imports
# ---------------

from textual.logging import TextualHandler

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Label, Button

#--------------
# local imports
# -------------

from . import __version__

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()

# -------------------
# Auxiliary functions
# -------------------

def arg_parser(name, version, description):
    # create the top-level parser
    parser = argparse.ArgumentParser(prog=name, description=description)
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, version))
    parser.add_argument('--console', action='store_true', help='Log to Textual dev. console.')
    parser.add_argument('--log-file', type=str, metavar="<FILE>", default=None, help='Log to file.')
    group0 = parser.add_mutually_exclusive_group()
    group0.add_argument('--verbose', action='store_true', help='Verbose output.')
    group0.add_argument('--quiet',   action='store_true', help='Quiet output.')
    return parser


def configure_logging(args):
    '''Configure the root logger'''
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO

    # set the root logger level
    log.setLevel(level)

    # Log formatter
    # fmt = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    # create console handler and set level to debug
    if args.console:
        ch = TextualHandler()
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


class QuestionApp(App[str]):
    def compose(self) -> ComposeResult:
        yield Label("Do you love Textual?")
        yield Button("Yes", id="yes", variant="primary")
        yield Button("No", id="no", variant="error")

    @on(Button.Pressed, '#yes')
    def yes_pressed(self) -> None:
        self.exit(return_code=3)


def main():
    '''The main entry point specified by pyproject.toml'''
    parser = arg_parser(
        name = __name__,
        version = __version__,
        description = "Example Textual App"
    )
   
    args = parser.parse_args(sys.argv[1:])
    configure_logging(args)
    app = QuestionApp()
    app.run()
    sys.exit(app.return_code or 0)