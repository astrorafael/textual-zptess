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
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch, ProgressBar
from textual.containers import Horizontal, Vertical

#--------------
# local imports
# -------------

from zptess.photometer import REF, TEST, label

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
        # Widget references in REF/TEST pairs
        self.log_w = [None, None]
        self.switch_w = [None, None]
        self.metadata_w = [None, None]
        self.progress_w = [None, None]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with Horizontal():
            with Horizontal():
                yield DataTable(id="ref_metadata")
                with Vertical():
                    yield Label("Photometer On/Off")
                    yield Switch(id="ref_phot")
                    yield Label("Ring Buffer")
                    yield ProgressBar(id="ref_ring", total=100, show_eta=False)
            with Horizontal():
                yield DataTable(id="tst_metadata")
                with Vertical():
                    yield Label("Photometer On/Off")
                    yield Switch(id="tst_phot")
                    yield Label("Ring Buffer")
                    yield ProgressBar(id="tst_ring", total=100, show_eta=False)
        yield Log(id="ref_log", classes="box")
        yield Log(id="tst_log", classes="box")
        

    def on_mount(self) -> None:
        # Apparently containers do not have a border_title to show
        for ident in ("#ref_metadata", "#tst_metadata"):
            table = self.query_one(ident)
            table.add_columns(*("Property", "Value"))
            table.fixed_columns = 2
            table.show_cursor = False
        self.log_w[REF] = self.query_one("#ref_log")
        self.log_w[TEST] = self.query_one("#tst_log")
        self.log_w[REF].border_title = f"{label(REF)} LOG"
        self.log_w[TEST].border_title = f"{label(TEST)} LOG"
        self.switch_w[REF] = self.query_one("#ref_phot")
        self.switch_w[TEST] = self.query_one("#tst_phot")
        self.switch_w[REF].border_title = 'ON'
        self.switch_w[TEST].border_title = 'ON'
        self.metadata_w[REF] =  self.query_one("#ref_metadata")
        self.metadata_w[TEST] = self.query_one("#tst_metadata")
        self.progress_w[REF] =  self.query_one("#ref_ring")
        self.progress_w[TEST] = self.query_one("#tst_ring")
        self.progress_w[REF].total = 75
        self.progress_w[TEST].total = 75
    
    def clear_metadata(self, role):
        self.metadata_w[role].clear()

    def append_log(self, role, line):
        self.log_w[role].write_line(line)

    def update_metadata(self, role, metadata):
        self.metadata_w[role].add_rows(metadata.items())

    def update_progress(self, role, amount):
        self.progress_w[role].advance(amount)
    
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
