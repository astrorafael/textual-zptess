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

# ----------------
# Module constants
# ----------------

_CSS_PKG = 'zptess.tui.resources.css'

_CSS_APP_FILE = 'mytextualapp.tcss'
_CSS_CAL_FILE = 'calibrate.tcss'

# Outside the Python packages
APP_CSS_PATH = os.path.join(os.getcwd(), _CSS_APP_FILE)
APP_CAL_PATH = os.path.join(os.getcwd(), _CSS_CAL_FILE)

_ABOUT_PKG = 'zptess.tui.resources.about'
_ABOUT_RES = 'description.md'


# Instead of a long, embeddded string, we read it as a Python resource
if sys.version_info[1] < 11:
    from pkg_resources import resource_string as resource_bytes
    DEFAULT_APP_CSS = resource_bytes(_CSS_PKG, _CSS_APP_FILE).decode('utf-8')
    DEFAULT_CAL_CSS = resource_bytes(_CSS_PKG, _CSS_CAL_FILE).decode('utf-8')
    ABOUT = resource_bytes(_ABOUT_PKG, _ABOUT_RES).decode('utf-8')
else:
    from importlib_resources import files
    DEFAULT_APP_CSS = files(_CSS_PKG).joinpath(_CSS_APP_FILE).read_text()
    DEFAULT_CAL_CSS = files(_CSS_PKG).joinpath(_CSS_CAL_FILE).read_text()
    ABOUT = files(_ABOUT_PKG).joinpath(_ABOUT_RES).read_text()
