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
from lica.textual.widgets.about import About
from lica.textual.widgets.label import WritableLabel

from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Label, Button, Static, Switch, ProgressBar, Sparkline, Rule
from textual.widgets import  Placeholder, TabbedContent, TabPane
from textual.containers import Horizontal, Vertical

#--------------
# local imports
# -------------

from ... import __version__
from .resources import DEFAULT_APP_CSS, APP_CSS_PATH, ABOUT
from .calibration import CalibrationPane
from .configure import ConfigurePane
from .export import ExportPane

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

class MyTextualApp(App[str]):

    TITLE = "ZPTESS"
    SUB_TITLE = "TESS-W Zero Point Calibration tool"

    # Seems the bindings are for the Footer widget
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "about", "About")
    ]

    DEFAULT_CSS = DEFAULT_APP_CSS
    CSS_PATH = APP_CSS_PATH

    def __init__(self, controller, description):
        self.controller = controller
        # Widget references in REF/TEST pairs
        self.log_w = [None, None]
        self.switch_w = [None, None]
        self.metadata_w = [None, None]
        self.progress_w = [None, None]
        self.graph_w = [None, None]
        self.SUB_TITLE = description
        super().__init__()


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with TabbedContent(initial="calibrate_tab"):
            with TabPane("Configure", id="config_tab"):
                yield ConfigurePane(id="config_pane")
            with TabPane("Calibrate", id="calibrate_tab"):
                yield CalibrationPane(id="calibrate_pane")
            with TabPane("Export", id="export_tab"):
                yield ExportPane(id="export_pane")


    def on_mount(self) -> None:
        self.log_w[Role.REF] = self.query_one("#ref_log")
        self.log_w[Role.TEST] = self.query_one("#tst_log")
        return

        # Apparently containers do not have a border_title to show
        for ident in ("#ref_metadata", "#tst_metadata"):
            table = self.query_one(ident)
            table.add_columns(*("Property", "Value"))
            table.fixed_columns = 2
            table.show_cursor = False
        
        

        self.graph_w[Role.REF] = self.query_one("#ref_graph")
        self.graph_w[Role.TEST] = self.query_one("#tst_graph")
        self.graph_w[Role.REF].border_title = f"{Role.REF} LOG"
        self.graph_w[Role.TEST].border_title = f"{Role.TEST} LOG"
        
        self.switch_w[Role.REF] = self.query_one("#ref_phot")
        self.switch_w[Role.TEST] = self.query_one("#tst_phot")
        self.switch_w[Role.REF].border_title = 'ON'
        self.switch_w[Role.TEST].border_title = 'ON'
        self.metadata_w[Role.REF] =  self.query_one("#ref_metadata")
        self.metadata_w[Role.TEST] = self.query_one("#tst_metadata")
        self.progress_w[Role.REF] =  self.query_one("#ref_ring")
        self.progress_w[Role.TEST] = self.query_one("#tst_ring")
        self.progress_w[Role.REF].total = 75
        self.progress_w[Role.TEST].total = 75
      
    
    def clear_metadata(self, role):
        self.metadata_w[role].clear()

    def append_log(self, role, line):
        self.log_w[role].write_line(line)

    def update_metadata(self, role, metadata):
        self.metadata_w[role].add_rows(metadata.items())

    def update_progress(self, role, amount):
        self.progress_w[role].advance(amount)

    def update_graph(self, role, data):
        self.graph_w[role].data = data

    # ======================
    # Textual event handlers
    # ======================

    def action_quit(self):
        self.controller.quit()

    def action_about(self):
        self.push_screen(About(self.TITLE, 
            version=__version__, 
            description=ABOUT))

    @on(Switch.Changed, "#ref_phot")
    def ref_switch_pressed(self, message):
        if message.control.value:
            self.controller.start_readings(Role.REF)
        else:
            self.controller.cancel_readings(Role.REF)

    @on(Switch.Changed, "#tst_phot")
    def tst_switch_pressed(self, message):
        if message.control.value:
            self.controller.start_readings(Role.TEST)
        else:
            self.controller.cancel_readings(Role.TEST)
