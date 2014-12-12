#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function

from config import *

import logging.config
import unittest

from ExergyUtilities.utility_inspect import get_self, get_parent

# Testing imports
from deap import design_space

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(format='%(funcName)-20s %(levelno)-3s: %(message)s', level=logging.DEBUG, datefmt='%I:%M:%S')
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#===============================================================================
# Unit testing
#===============================================================================

class DesignSpaceBasicTests(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(get_self())
        myLogger.setLevel("CRITICAL")
        print("Setup")
        myLogger.setLevel("DEBUG")

    def test010_SimpleCreation(self):
        print("**** TEST {} ****".format(get_self()))
        
