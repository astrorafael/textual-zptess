# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

from zptess import TEST, REF

def chop(string, sep=None):
    '''Chop a list of strings, separated by sep and 
    strips individual string items from leading and trailing blanks'''
    chopped = [ elem.strip() for elem in string.split(sep) ]
    if len(chopped) == 1 and chopped[0] == '':
    	chopped = []
    return chopped

def label(role):
	return  = REF.lower() if role == 'ref' else TEST.lower()