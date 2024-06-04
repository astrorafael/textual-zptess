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
from textual.containers import Horizontal

#--------------
# local imports
# -------------

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
    ("Name", "stars2"),
    ("Role", "TEST"),
    ("MAC address", "AA:BB:CC:DD:EE:FF"),
    ("Zero Point",  20.50),
    ("Freq. Offset", 0.0),
]

METADATA = {
    "Name": "stars2",
    "Role": "TEST",
    "MAC address": "AA:BB:CC:DD:EE:FF",
    "Zero Point":  20.50,
    "Freq. Offset": 0.0,
}

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
        with Horizontal(id="metadata_container"):
            yield DataTable(id="ref_metadata")
            yield DataTable(id="test_metadata")
        yield Log(id="ref_log", classes="box")
        yield Log(id="test_log", classes="box")
        #with ScrollableContainer(id="contenido"):
            #pass

    def on_mount(self) -> None:
        # Apparently containers do not have a border_title to show
        self.query_one("#metadata_container").border_title = "METADATA"
        for ident in ("#ref_metadata", "#test_metadata"):
            table = self.query_one(ident)
            table.add_columns(*("Property", "Value"))
            table.fixed_columns = 2
            table.show_cursor = False
        self.query_one("#ref_log").border_title = "REFERENCE LOG"
        self.query_one("#test_log").border_title = "TEST LOG"
     
    def get_log_widget(self, role):
        return self.query_one("#ref_log") if role == 'ref' else self.query_one("#test_log")

    def update_metadata(self, role, metadata):
        ident = "#ref_metadata" if role == 'ref' else "#test_metadata"
        table = self.query_one(ident)
        table.add_rows(metadata.items())
    
    def action_quit(self):
        self.quit_event.set()
        self.exit(return_code=2)

    @on(Button.Pressed, '#yes')
    def yes_pressed(self) -> None:
        self.exit(return_code=3)
