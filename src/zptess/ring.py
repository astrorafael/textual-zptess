# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import logging
import collections

# -------------------
# Third party imports
# -------------------


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

# -------
# Classes
# -------

class RingBuffer:

    def __init__(self, capacity=75):
        self._buffer = collections.deque([], capacity)

    def append(self, item):
        self._buffer.append(item)

    