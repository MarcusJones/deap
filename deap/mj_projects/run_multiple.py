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
import utility_executor as util_exec
import sys
import subprocess

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

    def test040_run_multiple_in_dir_execfile(self):
        print("**** TEST {} ****".format(whoami()))
        multiple_path = r"D:\Projects\PhDprojects\Multiple\ExplorationStudy2"
        print(multiple_path)

        def_book_paths = util_path.get_files_by_name_ext(multiple_path,'.','xlsx')

        commands = list()
        for path_book in def_book_paths:
            
            script_path = r"C:\Users\jon\git\deap1\deap\mj_projects\run_proj.py"
            full_call = ['python',  script_path, path_book]
            #print("RUNNING", full_call)
            commands.append(full_call)
            #raise
        update_delay = 2
        max_cpu_percent = 100
        max_processes = 4
        util_exec.execute_parallel(commands, update_delay, max_cpu_percent,max_processes)

        #subprocess.call(full_call, shell=False)

        