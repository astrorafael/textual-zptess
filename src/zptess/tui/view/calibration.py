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

import statistics

# ---------------
# Textual imports
# ---------------

from lica.asyncio.photometer import Model, Role
from lica.textual.widgets.label import WritableLabel

from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Log, DataTable, Label, Button, Static, Switch, ProgressBar, Sparkline, Rule
from textual.widgets import  TabbedContent, TabPane
from textual.containers import Horizontal, Vertical

#--------------
# local imports
# -------------

from .. import __version__
from .resources import DEFAULT_CAL_CSS, APP_CAL_PATH, APP_CSS_PATH

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)


# -------------------
# Auxiliary functions
# -------------------

class CalibrationPane(Static):

    DEFAULT_CSS = DEFAULT_CAL_CSS
    CSS_PATH = APP_CAL_PATH

    def __init__(self, *args, **kwargs):
        self.log_w = [None, None]
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield DataTable(id="ref_phot_info")
                with Vertical():
                    yield Label(f"{Role.REF.tag()} Photometer On/Off")
                    yield Switch(id="ref_phot")
                    yield Label("Ring Buffer")
                    yield ProgressBar(id="ref_ring", total=100, show_eta=False)
                    yield WritableLabel("<statistics here>")
                    yield Sparkline([], id="ref_graph", summary_function=statistics.median_low)
                yield Rule(orientation="vertical")
                yield DataTable(id="tst_phot_info")
                with Vertical():
                    yield Label(f"{Role.TEST.tag()} Photometer On/Off")
                    yield Switch(id="tst_phot")
                    yield Label("Ring Buffer")
                    yield ProgressBar(id="tst_ring", total=100, show_eta=False)
                    yield WritableLabel("<statistics here>")
                    yield Sparkline([], id="ref_graph", summary_function=statistics.median_low)
            with Horizontal(id="cal_horizontal"):
                 yield DataTable(id="stats_table")
                 with Horizontal():
                     yield Button.success("GO!", id="ok_button")
                     yield Button.error("Cancel", id="cancel_button")
            yield Log(id="ref_log")
            yield Log(id="tst_log")


    def on_mount(self) -> None:
        self.log_w[Role.REF] = self.query_one("#ref_log")
        self.log_w[Role.TEST] = self.query_one("#tst_log")
        self.log_w[Role.REF].border_title = f"{Role.REF.tag()} LOG"
        self.log_w[Role.TEST].border_title = f"{Role.TEST.tag()} LOG"
        self.stats_w = self.query_one("#stats_table")
        self.stats_w.add_columns(*("Round #", "Freq (Hz)", "Magnitude", "\u0394 Magnitude", "Zero Point"))
        self.stats_w.fixed_columns = 5
        self.stats_w.show_cursor = False
        self.ok_button_w = self.query_one("#ok_button")
        self.cancel_button_w = self.query_one("#cancel_button")
        for ident in ("#ref_phot_info", "#tst_phot_info"):
            table = self.query_one(ident)
            table.add_columns(*("Property", "Value"))
            table.fixed_columns = 2
            table.show_cursor = False

    def log(role, msg):
        self.log_w[role].write_line(line)
