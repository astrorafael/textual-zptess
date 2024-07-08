# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

import enum

from ._version import __version__

# ----------------
# Module constants
# ----------------


class CentralTendency(enum.Enum):
    MEDIAN = "median"
    MODE = "mode"
    MEAN = "mean"


SERIAL_PORT_PREFIX = "/dev/ttyUSB"

# TESS-W data

TEST_IP    = '192.168.4.1'
TEST_TCP_PORT = 23
TEST_UDP_PORT = 2255
TEST_SERIAL_PORT = 0
TEST_BAUD = 9600