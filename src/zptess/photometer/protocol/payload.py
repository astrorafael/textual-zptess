# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import re
import json
import logging
import datetime

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

# ----------------
# Module functions
# ----------------

# ----------
# Exceptions
# ----------


# -------
# Classes
# -------

class OldPayload:
    """
    Decodes Old Style TESS payload:
    <fH 04606><tA +2987><tO +2481><mZ -0000>
    """
    UNSOLICITED_RESPONSES = (
        {
            'name'    : 'Hz message',
            'pattern' : r'^<fH([ +]\d{5})><tA ([+-]\d{4})><tO ([+-]\d{4})><mZ ([+-]\d{4})>',       
        },
        {
            'name'    : 'mHz message',
            'pattern' : r'^<fm([ +]\d{5})><tA ([+-]\d{4})><tO ([+-]\d{4})><mZ ([+-]\d{4})>',       
        },
    )
    UNSOLICITED_PATTERNS = [ re.compile(ur['pattern']) for ur in UNSOLICITED_RESPONSES ]

    def __init__(self, parent):
        self.parent = parent
        self.log = parent.log
        self._prev_msg = None
        self._i = 1
        parent.log.info("%6s: Using %s decoder", parent.label, self.__class__.__name__)
     
    # ----------
    # Public API
    # ----------

    def decode(self, data: bytes, tstamp: datetime.datetime) -> (bool, dict):
        data = data.decode()
        self.parent.log.info("<== [%02d] %s", len(data), data)
        return self._handle_unsolicited_response(data, tstamp)
    
    # --------------
    # Helper methods
    # --------------

    def _match_unsolicited(self, line):
        '''Returns matched command descriptor or None'''
        for i, regexp in enumerate(self.UNSOLICITED_PATTERNS, 0):
            matchobj = regexp.search(line)
            if matchobj:
                self.parent.log.debug("matched %s", self.UNSOLICITED_RESPONSES[i]['name'])
                return self.UNSOLICITED_RESPONSES[i], matchobj
        return None, None


    def _handle_unsolicited_response(self, line, tstamp):
        '''
        Handle unsolicited responses from zptess.
        Returns True if handled, False otherwise
        '''
        ur, matchobj = self._match_unsolicited(line)
        if not ur:
            return False, None
        message = {}
        message['tamb']   = float(matchobj.group(2))/100.0
        message['tsky']   = float(matchobj.group(3))/100.0
        message['zp']     = float(matchobj.group(4))/100.0
        message['tstamp'] = tstamp
        message['udp'] = self._i
        self._i += 1
        if ur['name'] == 'Hz message':
            message['freq']   = float(matchobj.group(1))/1.0
            self.parent.log.debug("Matched {name}", name=ur['name'])
        elif ur['name'] == 'mHz message':
            message['freq'] = float(matchobj.group(1))/1000.0
            self.parent.log.debug("Matched {name}", name=ur['name'])
        else:
            return False, None
        prev_message = self._deduplicate(message)
        return True, message

    def _deduplicate(self, message):
        if self._prev_msg is None:
            self._prev_msg = message 
            return  False, None
        if message['tamb'] == self._prev_msg['tamb'] and message['tsky'] == self._prev_msg['tsky'] and message['freq'] == self._prev_msg['freq']:
            self.log.warn("Duplicate payload: %s", message)
            result = (False, None)
        else:
            result = (True, self._prev_msg)
        self._prev_msg = message    
        return result



class JSONPayload:
    """
    Decodes new JSON style TESS payload:
    """

    def __init__(self, parent):
        self.parent = parent
        self.log = parent.log
        self.log.info("%6s: Using %s decoder", parent.label, self.__class__.__name__)
        self._prev_msg = None

    # --------------
    # Helper methods
    # --------------

    def _deduplicate(self, message):
        if self._prev_msg is None:
            self._prev_msg = message
            return  False, None
        result = (True, self._prev_msg) if self._prev_msg['udp'] != message['udp'] else (False, None)
        if not result[0]:
            self.log.warn("Duplicate payload: %s", message)
        self._prev_msg = message    
        return result

    # ----------
    # Public API
    # ----------

    def decode(self, data: bytes, tstamp: datetime.datetime) -> (bool, dict):
        data = data.decode()
        self.log.info("<== [%02d] %s", len(data), data)
        try:
            message = json.loads(data)
        except Exception as e:
            return False, None
        else:
            if type(message) == dict:
                message['tstamp'] = tstamp
                flag, prev_message = self._deduplicate(message)
                return flag, prev_message
            else:
                return False, None


#---------------------------------------------------------------------
# --------------------------------------------------------------------
# --------------------------------------------------------------------



__all__ = [
    "JSONPayload",
    "OldPayload",
]
