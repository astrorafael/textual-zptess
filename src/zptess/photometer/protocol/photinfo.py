# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import re
import sys
import datetime
import logging

# -----------------
# Third Party imports
# -------------------

import anyio
import httpx

#--------------
# local imports
# -------------


from zptess import REF, TEST
from zptess.main import arg_parser, configure_logging

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__)


def formatted_mac(mac):
    ''''Corrects TESS-W MAC strings to be properly formatted'''
    return ':'.join(f"{int(x,16):02X}" for x in mac.split(':'))


class HTMLInfo:
    """
    Get the photometer by parsing the HTML photometer home page.
    Set the new ZP by using the same URL as the HTML form displayed for humans
    """
    CONFLICTIVE_FIRMWARE = ('Nov 25 2021 v 3.2',)

    GET_INFO = {
        # These apply to the /config page
        'name'  : re.compile(r"(stars\d+)"),       
        'mac'   : re.compile(r"MAC: ([0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2}:[0-9A-Fa-f]{1,2})"),       
        'zp'    : re.compile(r"(ZP|CI): (\d{1,2}\.\d{1,2})"),
         #'zp'    : re.compile(r"Const\.: (\d{1,2}\.\d{1,2})"),
        'freq_offset': re.compile(r"Offset mHz: (\d{1,2}\.\d{1,2})"),
        'firmware' : re.compile(r"Compiled: (.+?)<br>"),  # Non-greedy matching until <br>
        # This applies to the /setconst?cons=nn.nn page
        'flash' : re.compile(r"New Zero Point (\d{1,2}\.\d{1,2})"),   
    }

    def __init__(self, role, addr):
        self.log = logging.getLogger(__name__)
        self.addr = addr
        self.label = REF.lower() if role == 'ref' else TEST.lower()
        log.info("%s Using %s Info", self.label, self.__class__.__name__)

    # ---------------------
    # IPhotometerControl interface
    # ---------------------

    async def get_info(self, timeout=60):
        '''
        Get photometer information. 
        '''
        label = self.label
        result = {}
        result['tstamp'] = datetime.datetime.now(datetime.timezone.utc)
        url = self._make_state_url()
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            text = response.text
        matchobj = self.GET_INFO['name'].search(text)
        if not matchobj:
            self.log.error("%6s name not found!. Check unit's name", label)
        result['name'] = matchobj.groups(1)[0]
        matchobj = self.GET_INFO['mac'].search(text)
        if not matchobj:
            self.log.error("%6s MAC not found!", label)
        result['mac'] = formatted_mac(matchobj.groups(1)[0])
        matchobj = self.GET_INFO['zp'].search(text)
        if not matchobj:
            self.log.error("%6s ZP not found!", label)
        result['zp'] = float(matchobj.groups(1)[1]) # Beware the seq index, it is not 0 as usual. See the regexp!
        matchobj = self.GET_INFO['firmware'].search(text)
        if not matchobj:
            self.log.error("%6s Firmware not found!", label)
        result['firmware'] = matchobj.groups(1)[0]
        firmware = result['firmware']
        if firmware in self.CONFLICTIVE_FIRMWARE:
            pub.sendMessage('phot_firmware', role='test', firmware=firmware)
        matchobj = self.GET_INFO['freq_offset'].search(text)
        if not matchobj:
            self.log.warn("%6s Frequency offset not found, defaults to 0.0 mHz", label)
            result['freq_offset'] = 0.0
        else:
            result['freq_offset'] = float(matchobj.groups(1)[0])/1000.0
        return result


    async def save_zero_point(self, zero_point):
        '''
        Writes Zero Point to the device. 
        '''
        label = self.label
        result = {}
        result['tstamp'] = datetime.datetime.now(datetime.timezone.utc)
        url = self._make_save_url()
        params = [('cons', '{0:0.2f}'.format(zero_point))]
        # Paradoxically, the photometer uses an HTTP GET method tow wrte a ZP ....
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=4)
            text = response.text
        matchobj = self.GET_INFO['flash'].search(text)
        if not matchobj:
            raise IOError("{:6s} ZP not written!".format(label))
        result['zp'] = float(matchobj.groups(1)[0])
        return result

    # --------------
    # Helper methods
    # --------------

    def _make_state_url(self):
        return f"http://{self.addr}/config"

    def _make_save_url(self):
        return f"http://{self.addr}/setconst"


class DBasePhotometer:

    def __init__(self, role, dbase_url):
        self.log = logging.getLogger(__name__)
        self.url = dbase_url
        self.section = 'reference' if role == 'ref' else 'test'
        self.label = REF.lower() if role == 'ref' else TEST.lower()
        log.info("%6s Using %s Info", self.label, self.__class__.__name__)


    # ---------------------
    # IPhotometerControl interface
    # ---------------------

    async def save_zero_point(self, zero_point):
        '''
        Writes Zero Point to the device. 
        '''
        raise NotImplementedError()


    async def get_info(self, timeout):
        '''
        Get photometer information. 
        '''
        raise NotImplementedError()
        # label = self.label
        # self.log.info("==> {label:6s} [SQL] from config_t, section '{section}'", label=label, section=self.section)
        # result = yield self.config_dao.loadSection(self.section)
        # self.log.info("<== {label:6s} [SQL] returns {result}", label=label, result=result)
        # result['tstamp'] = datetime.datetime.now(datetime.timezone.utc)
        # result['zp']    = float(result['zp'])
        # result['freq_offset'] = float(result['freq_offset'])
        # result['old_proto'] = int(result['old_proto'])
        # return(result)


# -------------------
# Auxiliary functions
# -------------------
