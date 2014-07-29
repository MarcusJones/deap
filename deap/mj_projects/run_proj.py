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
import utility_path as util_path
import re
import deap as dp
import shutil
import utility_SQL_alchemy as util_sa
import sqlalchemy as sa
from deap.mj_utilities.db_base import DB_Base

import importlib
#===============================================================================
#--- Settings
#===============================================================================
def get_settings(book):
    with loggerCritical():
        all_data = book.get_table("Project")
    all_data = zip(*all_data)
    
    settings = book.get_row_as_dict(all_data,1)
    
    return settings

def build_structure(settings):
    
    #===========================================================================
    # Check root
    #===========================================================================
    if not os.path.exists(settings['run_root_directory']):
        os.makedirs(settings['run_root_directory'])
    
    
    
    #===========================================================================
    # Create sub dir for run
    #===========================================================================
    if settings['version_folders'] == 'Yes':
        this_rev_num = util_path.get_next_rev_number_dir(settings['run_root_directory'],settings['run_name'])
        this_rev_text = "{0:03d}".format(this_rev_num)
        path_run = os.path.join(settings['run_root_directory'], settings['run_name'] + this_rev_text)
        path_run = os.path.abspath(path_run)
        assert not os.path.exists(path_run), "{} exists".format(path_run)
        os.makedirs(path_run)
         
    else: 
        raise

    #===========================================================================
    # Create dirs of SQL and Matlab
    #===========================================================================
    path_sql = os.path.join(path_run,'SQL')
    #print(path_sql)
    if not os.path.exists(path_sql):
        os.makedirs(path_sql)
    path_sql_db = os.path.join(path_sql, 'results.sql')
    settings['path_sql_db'] = path_sql_db
    
    path_mlab = os.path.join(path_run,'Matlab')
    #print(path_sql)
    if not os.path.exists(path_mlab):
        os.makedirs(path_mlab)
    settings['path_matlab'] = path_mlab
    
    
    #===========================================================================
    # Copy over the project definition file
    #===========================================================================
    
    shutil.copyfile(settings['path_book'], os.path.join(path_run,'definition.xlsx'))
    
    #===========================================================================
    # Evolog
    #===========================================================================
    settings['path_evolog'] = os.path.join(path_run,'evolog.txt')
    
    #raise
    return settings
                
    #settings['run_root_directory']
    #if not util_path.check_path():
    #    util_path.create_dir()
    
    
    
    #rows = [row for row in all_data[2:] if row[0]]
    #row_nums = (xrange(1, 2+len(variable_rows)))        

#===============================================================================
#---Algorithm
#===============================================================================
def get_operators(book):
    with loggerCritical():
        all_data = book.get_table("Operators")
    operators = list()
    for operator_name in all_data[1:]:
        name = operator_name[0]
        operators_module = importlib.import_module('deap.mj_operators')
        operator_function = getattr(operators_module,name)
        logging.debug("Loaded {} operator".format(operator_function.__name__))
        operators.append(operators_module)
    return operators

def get_algorithm(book):
    with loggerCritical():
        all_data = book.get_table("Algorithm")
    print(all_data)    
#===============================================================================
#--- Mapping 
#===============================================================================
def get_design_space(definitionBookPath):
        basisVariables = get_variables(definitionBookPath)
        objectives = get_objectives(definitionBookPath)
        thisDspace = DesignSpace(basisVariables,objectives)
        
        return thisDspace

def get_list_variables(book):
    with loggerCritical():
        all_data = book.get_table("List Variables")
    if len(all_data) == 1:
        return None
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

def get_fitness(book):
    with loggerCritical():
        all_data = book.get_table("Objectives")
    objective_rows = [row for row in all_data[1:] if row[0]]
    #print(objective_rows)
    row_nums = (xrange(1, 1+len(objective_rows)))
    
    names = list()
    weights = list()
    for rownum in row_nums:
        obj_def = book.get_row_as_dict(all_data,rownum, flg_length_mismatch = True)
        #print(obj_def)
        names.append(obj_def['Name'])
        weights.append(float(obj_def['Weight']))

    dp.creator.create("Fitness", dp.base.Fitness, weights=(-1.0, -1.0), names = ('obj1', 'obj2'))
    
    #print(globals())
    
    return dp.creator.Fitness
        
    #ds.Fitness(weights=weights, names=names)


def get_objectives(fitness):
    # Create OSpace from Fitness
    objs = list()
    for name,weight in zip(fitness.names,fitness.weights):
        objs.append(ds.Objective(name,weight))
    this_obj_space = ds.ObjectiveSpace(objs)
    #session.add_all(objs)    
        
    return this_obj_space

#===============================================================================
#--- Get whole project
#===============================================================================

def get_project_def(path_book):
    book = util_excel.ExcelBookRead2(path_book)         

    #===========================================================================
    #---Settings
    #===========================================================================
    settings = get_settings(book)
    settings['path_book'] = path_book

    settings = build_structure(settings)
    
    for k,v, in settings.iteritems():
       print("{:>30} : {:<30} {}".format(k,v, type(v)))
    
    #===========================================================================
    #---Database
    #===========================================================================
    engine = sa.create_engine("sqlite:///{}".format(settings['path_sql_db']), echo=0, listeners=[util_sa.ForeignKeysListener()])
    Session = sa.orm.sessionmaker(bind=engine)
    session = Session()
    
    with open(settings['path_evolog'], 'w+') as evolog:
        print("Start log", file=evolog)
    
    
    #===========================================================================
    #---DesignSpace, ObjectiveSpace
    #===========================================================================
    variables = list()
    list_vars = get_list_variables(book)
    if list_vars:
        variables.extend(list_vars)
    range_vars = variables.extend(get_range_variables(book))
    if range_vars:
        variables.extend(range_vars)
    
    design_space = ds.DesignSpace(variables)
    
    # Get ObjectiveSpace
    Fitness = get_fitness(book)
    
    objective_space = get_objectives(Fitness)
    
    #===========================================================================
    #---Mapping
    #===========================================================================
    mapping = ds.Mapping(design_space, objective_space)
    res_ORM_table = ds.generate_individuals_table(mapping)
    Results = ds.generate_ORM_individual(mapping)
    sa.orm.mapper(Results, res_ORM_table) 

    DB_Base.metadata.create_all(engine)
    session.commit()
    
    mapping.assign_fitness(Fitness)
    
    #===========================================================================
    #---Operators
    #===========================================================================
    get_operators(book)

    #===========================================================================
    #--Algorithm
    #===========================================================================
    get_algorithm(book)
    
#===============================================================================
# Unit testing
#===============================================================================

class allTests(unittest.TestCase):

    def setUp(self):
        print("**** TEST {} ****".format(whoami()))
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.path_book = os.path.abspath(curr_dir + r'\..\tests\testing_zdt1.xlsx')
        #self.book = util_excel.ExcelBookRead2(self.path_book)            
        #print(self.book)
        
    def test010_SimpleCreation(self):
        print("**** TEST {} ****".format(whoami()))

        get_project_def(self.path_book)
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
