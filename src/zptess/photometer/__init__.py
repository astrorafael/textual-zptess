# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# ---------
# Constants
# ---------

# Photometer roles
REF  = 0
TEST = 1

TEST_LABEL = 'TEST'
REF_LABEL  = 'REF.'

def label(role):
	return REF_LABEL.lower() if role == REF else TEST_LABEL.lower()