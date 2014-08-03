import os
import shutil
import utility_file as util_file
from math import sqrt
import subprocess
import datetime
from UtilityLogger import loggerCritical

from config import *


#===============================================================================
# Logging
#===============================================================================
import logging.config
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#===============================================================================
#---Pre processing
#===============================================================================
def pre_process_empty(self, settings):
    pass


def pre_process_exe(self, settings):
    """For simulation runs, create the directory structure needed to simulate
    """
    assert os.path.exists(settings['path_exe']), "EXE does not exist; {}".format(settings['path_exe'])
    assert os.path.exists(settings['path_template']), "Template does not exist; {}".format(settings['path_template'])
    #===========================================================================
    # Check paths
    #===========================================================================
    #logging.debug("Evaluating {}".format(self.hash))

    #===========================================================================
    # Assign life-cycle
    #===========================================================================

    this_ind_sub_dir = os.path.join(settings['run_full_path'],"individuals","{}".format(self.hash))
    
    os.makedirs(this_ind_sub_dir)
    
    self.path_input_file = os.path.join(this_ind_sub_dir,'input.txt')
    self.path_output_file = os.path.join(this_ind_sub_dir,'output.txt')
    
    shutil.copy(settings['path_template'], self.path_input_file)

    exe_str = "{} -i {} -o {}".format(settings['path_exe'], self.path_input_file, self.path_output_file)
    
    #===========================================================================
    # Apply changes
    #===========================================================================
    input_file_obj = util_file.FileObject(self.path_input_file)
    
    replacements = list()
    for allele in self.chromosome:
        find_val = "{}{}".format(settings['replace_sigil'],allele.name)
        repl_val = allele.value
        replacements.append([find_val,repl_val])
        
    #print(replacements)
    with loggerCritical():
        input_file_obj.makeReplacements(replacements)

    input_file_obj.writeFile(input_file_obj.filePath)
    
    self.directory = this_ind_sub_dir
    self.execution_command = exe_str
    
    logging.debug("{} - {}".format(self.hash, self.execution_command))
    
    return self

#===============================================================================
#---Execution    
#===============================================================================
def execute_simple(self, settings):
    """For mathematical evaluations
    """
    pass

def execute_exe(self,settings):

    
    self.process = subprocess.Popen(self.execution_command, shell=True)
    self.PID = self.process.pid
    self.start_time = datetime.datetime.now()
    logging.debug("Executing {}".format(self))


#===============================================================================
#---Post process
#===============================================================================
def post_process_empty(self, settings):
    pass

def post_process_exe(self, settings):
    logging.debug("Post processing {}, {}".format(self.hash, self.path_output_file))
    #print(self)
    
    with open(self.path_output_file, 'r') as fh:
        lines = fh.readlines()
        #print(lines)
        assert(len(lines) == 1)
        line = lines[0].strip()
        results = [float(res) for res in line.split(',')]
        #print(results)
    
    
    self.fitness.setValues(results)
        
    
    
    #raise
    return self


#===============================================================================
#---Executors
#===============================================================================
def execute_zdt1(self,settings):
    values = list(self[:])

    try:
        values = [float(val.value) for val in values]
    except AttributeError:
        pass

    g  = 1.0 + 9.0*sum(values[1:])/(len(values)-1)
    f1 = values[0]
    f2 = g * (1 - sqrt(f1/g))
    
    self.fitness.setValues((f1, f2))

    #logging.debug("Evaluated {} -> {}".format(values, self.fitness))
    
    return self


#===============================================================================
#---Evaluators
#===============================================================================
"""ZDT1 multiobjective function.

:math:`g(\\mathbf{x}) = 1 + \\frac{9}{n-1}\\sum_{i=2}^n x_i`

:math:`f_{\\text{ZDT1}1}(\\mathbf{x}) = x_1`

:math:`f_{\\text{ZDT1}2}(\\mathbf{x}) = g(\\mathbf{x})\\left[1 - \\sqrt{\\frac{x_1}{g(\\mathbf{x})}}\\right]`
"""

mj_zdt1_decimal = {
                   'pre_process' : pre_process_empty,
                   'execute' : execute_zdt1,
                   'post_process' : post_process_empty,
                   } 



mj_zdt1_decimal_exe = {
                       'pre_process' : pre_process_exe,
                       'execute' : execute_exe,
                       'post_process' : post_process_exe,
                       }
