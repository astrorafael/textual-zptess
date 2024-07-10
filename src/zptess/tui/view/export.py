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
from textual.widgets import DataTable, Label, Button, Static, Switch, ProgressBar, Sparkline, Rule, Placeholder
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

class ExportPane(Static):

    def compose(self) -> ComposeResult:
        yield Placeholder()

    def on_mount(self) -> None:
        pass