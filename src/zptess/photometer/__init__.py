# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# ---------
# Constants
# ---------

# Photometer roles
REF  = 1
TEST = 0

TEST_LABEL = 'TEST'
REF_LABEL  = 'REF.'

def label(role):
	return REF_LABEL.upper() if role == REF else TEST_LABEL.upper()

# By exclusive OR
def other(role):
	return 1 ^ role