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

from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch
from textual.containers import Horizontal

#--------------
# local imports
# -------------

from zptess.photometer import REF, TEST

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

class ZpTessApp(App[str]):

    TITLE = "ZPTESS"
    SUB_TITLE = "TESS-W Zero Point Calibration tool"

    # Seems the bindings are for the Footer widget
    BINDINGS = [
        ("q", "quit", "Quit Application")
    ]

    CSS_PATH = [
        os.path.join("css", "zptess.tcss"),
    ]

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with Horizontal():
            with Horizontal():
                yield DataTable(id="ref_metadata")
                yield Switch(id="ref_phot")
            with Horizontal():
                yield DataTable(id="tst_metadata")
                yield Switch(id="tst_phot")
        yield Log(id="ref_log", classes="box")
        yield Log(id="tst_log", classes="box")
        

    def on_mount(self) -> None:
        # Apparently containers do not have a border_title to show
        for ident in ("#ref_metadata", "#tst_metadata"):
            table = self.query_one(ident)
            table.add_columns(*("Property", "Value"))
            table.fixed_columns = 2
            table.show_cursor = False
        self.ref_log = self.query_one("#ref_log")
        self.tst_log = self.query_one("#tst_log")
        self.ref_switch = self.query_one("#ref_phot")
        self.tst_switch = self.query_one("#tst_phot")
        self.ref_log.border_title = "REFERENCE LOG"
        self.tst_log.border_title = "TEST LOG"
        self.ref_switch.border_title = "ON/OFF"
        self.tst_switch.border_title = "ON/OFF"
    
    def clear_metadata(self, role):
        widget = self.query_one("#ref_metadata") if role == REF else self.query_one("#tst_metadata")
        widget.clear()


    def get_log_widget(self, role):
        return self.ref_log if role == REF else self.tst_log

    def update_metadata(self, role, metadata):
        ident = "#ref_metadata" if role == REF else "#tst_metadata"
        table = self.query_one(ident)
        table.add_rows(metadata.items())
    
    def action_quit(self):
        self.controller.quit_event.set()
        self.exit(return_code=2)


    @on(Switch.Changed, "#ref_phot")
    def ref_switch_pressed(self, message):
        if message.control.value:
            self.controller.start_readings(REF)
        else:
            self.controller.cancel_readings(REF)

    @on(Switch.Changed, "#tst_phot")
    def tst_switch_pressed(self, message):
        if message.control.value:
            self.controller.start_readings(TEST)
        else:
            self.controller.cancel_readings(TEST)
