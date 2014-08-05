#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function

from config import *

import logging.config
import unittest

from utility_inspect import whoami, whosdaddy, listObject

# Testing imports
from ..design_space import Variable, DesignSpace

from run_proj import run_project_def
import utility_path as util_path

import sys


#===============================================================================
# Logging
#===============================================================================
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#===============================================================================
# Unit testing
#===============================================================================

class Tests(unittest.TestCase):
    def setUp(self):
        print("**** TEST {} ****".format(whoami()))
        #myLogger.setLevel("CRITICAL")
        #print("Setup")
        #myLogger.setLevel("DEBUG")

    def test010_SimpleCreation(self):
        print("**** TEST {} ****".format(whoami()))

    
    def test040_run_multiple_in_dir_execfile(self):
        print("**** TEST {} ****".format(whoami()))
        multiple_path = r"D:\Projects\PhDprojects\Multiple"
        multiple_path = r"D:\Projects\PhDprojects\Multiple\this_test"
        #rootPath, search_name, search_ext
        def_book_paths = util_path.get_files_by_name_ext(multiple_path,'.','xlsx')
        for path_book in def_book_paths:
            print("RUNNING", path_book)
            run_project_def(path_book)
            #path_sql
        #print(files)
        
        