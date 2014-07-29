#===============================================================================
# Title of this Module
# Authors; MJones, Other
# 00 - 2012FEB05 - First commit
# 01 - 2012MAR17 - Update to ...
#===============================================================================

"""This module does A and B.
Etc.
"""

#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function

from config import *

import logging.config
import unittest
import deap.design_space as ds

import utility_excel as util_excel
from utility_inspect import whoami, whosdaddy, listObject
from UtilityLogger import loggerCritical,loggerDebug

#===============================================================================
# Code
#===============================================================================
def get_list_variables(book):
    with loggerCritical():
        all_data = book.get_table("List Variables")
    variable_rows = [row for row in all_data[2:] if row[0]]
    row_nums = (xrange(1, 2+len(variable_rows)))
    
    variables = list()
    for i, rownum in enumerate(row_nums):
        variable_def = book.get_row_as_dict(all_data,rownum, num_cols = 3, flg_length_mismatch = False)
        list_vals = [item for item in all_data[rownum] if item != ""]
        list_vals = list_vals[3:]
        thisVar = ds.Variable.ordered(variable_def['Name'],variable_def['Type'],list_vals)
        variables.append(thisVar)

#        else: raise
#    elif variable_def['Creation'] == "List": # List
#         values = tuple([var for var in variable_def[3:] if var])
#         name = variable_def['Name']
#         vtype = variable_def['Type']
#         thisVar = ds.Variable.ordered(name, locus, vtype,values)
#         variables.append(thisVar)
#     else: raise

    return variables


def get_range_variables(book):
    with loggerCritical():
        all_data = book.get_table("Range Variables")
    variable_rows = [row for row in all_data[2:] if row[0]]
    row_nums = (xrange(1, 2+len(variable_rows)))

    variables = list()
    for i, rownum in enumerate(row_nums):
        variable_def = book.get_row_as_dict(all_data,rownum, flg_length_mismatch = True)
        thisVar = ds.Variable.from_range(variable_def['Name'], variable_def['Type'], str(variable_def['MIN']), str(variable_def['STEP']), str(variable_def['MAX']))
        variables.append(thisVar)

    return variables

def get_objectives(book):
    allData = book.get_table("Objectives")
    objectiveDefRows = [row for row in allData[1:] if row[0]]
    
    objList = list()
    for objDef in objectiveDefRows:
        objList.append(objDef[0])

    return objList

def get_design_space(definitionBookPath):
        basisVariables = get_variables(definitionBookPath)
        objectives = get_objectives(definitionBookPath)
        thisDspace = DesignSpace(basisVariables,objectives)
        
        return thisDspace

def get_project_def(book):
    allData = book.get_table("Project")
    
    variables = list()
    variables.extend(get_list_variables(book))
    variables.extend(get_range_variables(book))
    
    ds.DesignSpace(variables)
    
    raise
    dictionaryRows = [row for row in allData[1:] if row[0]]

    settings = dict(dictionaryRows)
    
    if settings["Type"] == "Global Search":
        settings["Controller"] = cntrl_globalSearch

    elif settings["Type"] == "Random Search":
        settings["Controller"] = Controller_randomSearch
        
    elif settings["Type"] == "Basic Evolution":
        settings["Controller"] = cntrl_basicEvolutionary
        
    else:
        raise Exception("Project type {} does not exist".format(settings["Type"]))
    
    #if settings["Individual"] == "Math":
    #    settings["evaluator"] = sumMaxFitness
    #print repr(settings["Type"])
    #print repr(str(settings["Type"]))

    
    return settings



#===============================================================================
# Unit testing
#===============================================================================

class allTests(unittest.TestCase):

    def setUp(self):
        print("**** TEST {} ****".format(whoami()))
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        path_book = os.path.abspath(curr_dir + r'\..\tests\testingRandomSearch.xlsx')
        self.book = util_excel.ExcelBookRead2(path_book)            
        print(self.book)
        
    def test010_SimpleCreation(self):
        print("**** TEST {} ****".format(whoami()))

        get_project_def(self.book)
#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(ABSOLUTE_LOGGING_PATH)
    logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
    

    myLogger = logging.getLogger()
    myLogger.setLevel("DEBUG")

    logging.debug("Started _main".format())
    
    #print FREELANCE_DIR
    
    unittest.main()

    logging.debug("Finished _main".format())
