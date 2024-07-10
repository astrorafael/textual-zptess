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

from .. import __version__
from .resources import DEFAULT_CAL_CSS, DEFAULT_APP_CSS, APP_CAL_PATH, APP_CSS_PATH, ABOUT

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

class ConfigPane(Static):

    def compose(self) -> ComposeResult:
        yield Placeholder()

    def on_mount(self) -> None:
        pass

class CalibPane(Static):

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
        

class ExportPane(Static):

    def compose(self) -> ComposeResult:
        yield Placeholder()

    def on_mount(self) -> None:
        pass

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
        with Horizontal():
            with Horizontal():
                yield DataTable(id="ref_metadata")
                with Vertical():
                    yield Label("Photometer On/Off", classes="mylabels")
                    yield Switch(id="ref_phot")
                    yield Label("Ring Buffer", classes="mylabels")
                    yield ProgressBar(id="ref_ring", total=100, show_eta=False)
            with Horizontal():
                yield DataTable(id="tst_metadata")
                with Vertical():
                    yield Label("Photometer On/Off", classes="mylabels")
                    yield Switch(id="tst_phot")
                    yield Label("Ring Buffer", classes="mylabels")
                    yield ProgressBar(id="tst_ring", total=100, show_eta=False)
        with TabbedContent(initial="logs"):
            with TabPane("Logs", id="logs"):
                yield Log(id="ref_log", classes="box")
                yield Log(id="tst_log", classes="box")
            with TabPane("Graphs", id="graphs"):
                yield Sparkline([], id="ref_graph", summary_function=statistics.median_low)
                yield Rule(line_style="dashed")
                yield Sparkline([], id="tst_graph", summary_function=statistics.median_low)
        yield Footer()


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        with TabbedContent(initial="calibrate_tab"):
            with TabPane("Configure", id="config_tab"):
                yield ConfigPane(id="config_pane")
            with TabPane("Calibrate", id="calibrate_tab"):
                yield CalibPane(id="calibrate_pane")
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
