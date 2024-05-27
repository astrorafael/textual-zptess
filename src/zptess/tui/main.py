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
import argparse
import logging

# ---------------
# Textual imports
# ---------------

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static
from textual.containers import ScrollableContainer

#--------------
# local imports
# -------------

from zptess import __version__
from zptess.utils.argsparse import args_parser
from zptess.utils.logging import configure

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

ROWS = [
    ("Property", "Value"),
    ("Name", "stars1"),
    ("Role", "TEST"),
    ("MAC address", "AA:BB:CC:DD:EE:FF"),
    ("Zero Point",  20.50),
    ("Freq. Offset", 0.0),
]


class ZpTessApp(App[str]):

    TITLE = "ZPTESS"
    SUB_TITLE = "TESS-W Zero Point Calibration tools"

    # Seems the bindings are for the Footer widget
    BINDINGS = [
        ("q", "quit", "Quit Application")
    ]

    CSS_PATH = [
        os.path.join("css", "zptess.tcss"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        yield DataTable()
        yield Log(id="reflog")
        yield Log(id="testlog")
        #with ScrollableContainer(id="contenido"):
            #pass

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])
      
    def action_quit(self):
        self.exit(return_code=2)

    @on(Button.Pressed, '#yes')
    def yes_pressed(self) -> None:
        self.exit(return_code=3)


def main():
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = "Example Textual App"
    )
   
    args = parser.parse_args(sys.argv[1:])
    configure(args)
    app = ZpTessApp()
    app.run()
    sys.exit(app.return_code or 0)