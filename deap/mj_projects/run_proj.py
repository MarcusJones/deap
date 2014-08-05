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

import sys
sys.path.append(r'C:\Users\jon\git\deap1\deap')

from config import *

import unittest
import design_space as ds

import utility_excel as util_excel
from utility_inspect import whoami, whosdaddy, listObject
from UtilityLogger import loggerCritical,loggerDebug
import utility_path as util_path
import re
import deap as dp
import shutil
import utility_SQL_alchemy as util_sa
import mj_utilities.util_db_process as util_proc
import sqlalchemy as sa
from mj_utilities.db_base import DB_Base
import cProfile
import time 
import subprocess

import numpy as np


import importlib

#===============================================================================
# Logging
#===============================================================================
import logging.config
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#===============================================================================
#--- Settings
#===============================================================================
def get_settings(book):
    with loggerCritical():
        all_data = book.get_table("Project")
    all_data = zip(*all_data)
    
    settings = book.get_row_as_dict(all_data,1)
    settings['excel_path'] = book.excelPath
    
    return settings

def build_structure(settings):
    
    if settings['continue_run'] == 'Yes':
        
        # Get the path of the excel file, which is always stored at the root of project
        settings['run_full_path'] = os.path.split(settings['excel_path'])[0]
        
        #run_root_directory
        assert(os.path.exists(settings['run_root_directory']))
        
        path_sql = os.path.join(settings['run_full_path'],'SQL','')
        path_sql_db = os.path.join(path_sql, 'results.sql')
        settings['path_sql_db'] = path_sql_db
        
        path_mlab = os.path.join(settings['run_root_directory'],'Matlab')
        settings['path_matlab'] = path_mlab
        
        settings['path_evolog'] = os.path.join(settings['run_full_path'],'evolog.txt')
        
        assert os.path.exists(settings['run_root_directory']), "{}".format(settings['run_root_directory'])
        assert os.path.isfile(settings['path_sql_db']), "{}".format(settings['path_sql_db'])
        settings['existing_db'] = 'Yes'
        assert os.path.exists(settings['run_full_path']), "{}".format(settings['path_matlab'])
        assert os.path.isfile(settings['path_evolog']), "{}".format(settings['path_evolog'])
        
        return settings
    elif settings['delete_folder']== 'Yes':
        raise
    else:
        pass
    
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
        settings['run_full_path'] = path_run
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
    settings['existing_db'] = 'No'

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
    
    return settings

#===============================================================================
#---Algorithm
#===============================================================================
def get_operators(book):
    with loggerCritical():
        all_data = book.get_table("Operators")
        
    operators_def = dict()
    #print(all_data)
    for row in all_data:
        operators_def[row[0]] = {'module' : row[1],'function' : row[2]}

    for k,v in operators_def.iteritems():
        #this_mod = importlib.import_module('deap.' + operators_def[k]['module'])
        operators_def[k] = getattr(importlib.import_module('deap.' + operators_def[k]['module']), operators_def[k]['function'])

    logging.debug("Operators loaded:")
    for item,function in operators_def.iteritems():
        logging.debug("{:>20} - {}".format(item,function.__name__))
                
    return operators_def
#     raise        
#     operators = list()
#     for operator_name in all_data[1:]:
#         name = operator_name[0]
#         operators_module = importlib.import_module('deap.mj_operators')
#         operator_function = getattr(operators_module,name)
#         logging.debug("Loaded {} operator".format(operator_function.__name__))
#         operators.append(operators_module)
#     return operators

def get_algorithm(book):
    with loggerCritical():
        all_data = book.get_table("Algorithm")
    
    algorithm_def = dict()
    for row in all_data:
        algorithm_def[row[0]] = {'module' : row[1],'function' : row[2]}
        
    for k,v in algorithm_def.iteritems():
        #this_mod = importlib.import_module('deap.' + algorithm_def[k]['module'])
        algorithm_def[k] = getattr(importlib.import_module('deap.' + algorithm_def[k]['module']), algorithm_def[k]['function'])
        
    logging.debug("Algorithm loaded:")
    for item,function in algorithm_def.iteritems():
        logging.debug("{:>20} - {}".format(item,function))

    return algorithm_def


def get_parameters(book):
    with loggerCritical():
        all_data = book.get_table("Parameters")
    
    parameters_def = dict()
    for row in all_data[1:]:
        parameters_def[row[0]] = {'value' : row[1],'type' : row[2]}
    
    for k,v in parameters_def.iteritems():
        if v['type'] == 'int':
            parameters_def[k] = int(v['value'])
        elif v['type'] == 'float':
            parameters_def[k] = v['value']       
        else:
            
            raise Exception("Unknown {}".format(v['type']))

    
    #print(parameters_def)
    #raise
    #settings = book.get_row_as_dict(all_data,1)
    
    return parameters_def



#===============================================================================
#--- Mapping 
#===============================================================================
def get_list_variables(book):
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

    return variables


def get_range_variables(book):
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

    return objs

#===============================================================================
#--- Get whole project
#===============================================================================

def run_project_def(path_book):
    with util_excel.ExcelBookRead2(path_book) as book:         
        print("Running this book: {}".format(book))
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
        print("**************",engine)
        Session = sa.orm.sessionmaker(bind=engine)
        session = Session()
        
        logging.debug("Initialized session {} with SQL alchemy version: {}".format(engine, sa.__version__))
    
        with open(settings['path_evolog'], 'w+') as evolog:
            print("Start log", file=evolog)
        
        
        #===========================================================================
        #---DesignSpace, ObjectiveSpace
        #===========================================================================
        with loggerCritical():
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
        
        objs = get_objectives(Fitness)
        objective_space = ds.ObjectiveSpace(objs)
    
        # Add vectors to DB
        if settings['existing_db'] == 'No':
            for var in design_space.basis_set:
                session.add_all(var.variable_tuple)
            session.add_all(objs)    
        
            # Add the variable names to the DB
            session.add_all(design_space.basis_set)
    
        #===========================================================================
        #---Operators
        #===========================================================================
        operators = get_operators(book)
    
        #===========================================================================
        #---Algorithm
        #===========================================================================
    
        algorithm = get_algorithm(book)
        
        parameters = get_parameters(book)
        for k,v, in parameters.iteritems():
           print("{:>30} : {:<30} {}".format(k,v, type(v)))
            
    #===========================================================================
    #---Mapping
    #===========================================================================
    mapping = ds.Mapping(design_space, objective_space)
    res_ORM_table = ds.generate_individuals_table(mapping)
    Results = ds.generate_ORM_individual(mapping)
    sa.orm.mapper(Results, res_ORM_table) 
    
    DB_Base.metadata.create_all(engine)
    for item in session.new:
        print(item)
    #raise
    session.commit()
    
    mapping.assign_fitness(Fitness)
    mapping.assign_individual(ds.Individual2)
    mapping.assign_evaluator(algorithm['life_cycle'])

    
    #===========================================================================
    #---Execute    
    #===========================================================================
    
    algorithm['name'](settings=settings, 
                      algorithm=algorithm,
                      parameters=parameters,
                      operators=operators, 
                      mapping=mapping, 
                      session=session,
                      Results=Results)
     
    
    

    #===========================================================================
    # Post process
    #===========================================================================
    util_proc.process_db_to_mat(settings['path_sql_db'],settings['path_matlab'])
    
    
    
    #===========================================================================
    #---asdf
    #===========================================================================
    if 0:
        session.commit()
        print(engine.table_names())
        
        #engine.dispose()
        #DB_Base.metadata.drop_all()
        #meta = sa.MetaData(bind = engine)
        #meta.reflect()
        #meta.drop_all()
        #session.close()
        
    #     print(DB_Base)
    #     for k in dir(DB_Base):
    #         print(k)    
    #     for k in dir(DB_Base.metadata):
    #         print(k)    
    #     for k,v in DB_Base.iteritems():
    #         print(k,v)
        #print('DB_Base.metadata', DB_Base.metadata)
        #print('DB_Base.metadata.bind',DB_Base.metadata.bind)
        DB_Base.metadata.bind = engine
        #print('DB_Base.metadata.bind',DB_Base.metadata.bind)
        #print(DB_Base.metadata.bind(engine))
        DB_Base.metadata.reflect()
        print("DB_Base:")
        for k in dir(DB_Base):
            print(k)
        print("DB_Base.metadata:")
        for k in dir(DB_Base.metadata):
            print(k)   
        DB_Base.metadata.drop_all()
        
        session.close()
        print(engine.table_names())
        raise
        
        #logging.debug("Done with {}".format(engine, sa.__version__))
    
        
    
def my_range(start, stop, step):
    this_list = [float(num) for num in np.arange(start, stop, step)] + [stop] 
    return this_list

def parameterize_excel_def(template_path,target_path):
    
    mod1 = ['Parameters', 'Probability crossover']
    mod1 = [mod1 + [this_p] for this_p in my_range(0.1, 1, 0.1)]
    #mod1 = mod1 * 10

    modifications = list()
    for row in mod1:
        modifications.append(dict(zip(['Sheet', 'Parameter', 'Value'],row)))
    
    for row in  modifications:
        print(row)
    #raise
    
    for i,mod in enumerate(modifications):
        print('This mod: {}'.format(mod))
        name = 'Definition'+str(i)+'.xlsx'
        with util_excel.ExcelBookAPI(template_path) as book:            
            this_target_path = os.path.join(target_path,name)
        this_book = book.clone(this_target_path)
        print('This book: {}'.format(this_book))
        target_row = this_book.scanDown2(mod['Sheet'], 1, 1, mod['Parameter'], limitScan=100)
        target_col = 2
        this_book.write_one(mod['Sheet'],target_row,target_col,mod['Value'])
        this_book.save_and_close_no_warnings()

    
#===============================================================================
# Unit testing
#===============================================================================

class allTests(unittest.TestCase):

    def setUp(self):
        print("**** TEST {} ****".format(whoami()))
        self.curr_dir = os.path.dirname(os.path.realpath(__file__))
        
    def test010_testing_zdt1(self):
        print("**** TEST {} ****".format(whoami()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\testing_zdt1.xlsx')
        run_project_def(path_book)
        
    def test020_nsga1_zdt1_Xbinary_Mbinary(self):
        print("**** TEST {} ****".format(whoami()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary.xlsx')
        run_project_def(path_book)

    def test021_nsga1_zdt1_Xbinary_Mbinary_SMALL(self):
        print("**** TEST {} ****".format(whoami()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary SMALL.xlsx')
        run_project_def(path_book)


    def test030_nsga1_zdt1_Xbinary_Mbinary_EXE(self):
        print("**** TEST {} ****".format(whoami()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary_EXE.xlsx')
        run_project_def(path_book)
    
    def test040_run_multiple_in_dir(self):
        print("**** TEST {} ****".format(whoami()))
        multiple_path = r"D:\Projects\PhDprojects\Multiple"
        multiple_path = r"D:\Projects\PhDprojects\Multiple\this_test"
        #rootPath, search_name, search_ext
        def_book_paths = util_path.get_files_by_name_ext(multiple_path,'.','xlsx')
        for path_book in def_book_paths:
            time.sleep(2)
            print("RUNNING", path_book)
            run_project_def(path_book)
            #path_sql
        #print(files)


    
    def test100_Postprocess(self):
        print("**** TEST {} ****".format(whoami()))
        path_sql = r"D:\Projects\PhDprojects\testZDT1exe\Run168\SQL\results.sql"
        path_mlab = r"D:\Projects\PhDprojects\testZDT1exe\Run168\Matlab"
        util_proc.process_db_to_mat(path_sql,path_mlab)
        
    def test200_parameterize_excel(self):
        path_template = r'D:\Projects\PhDprojects\Multiple\Template1.xlsx'
        path_target_dir = r'D:\Projects\PhDprojects\Multiple\this_test\\'
        parameterize_excel_def(path_template,path_target_dir)
        
    def test300_Profile(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        path_book = os.path.abspath(curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary.xlsx')
        print("Profile")
        cProfile.run('run_project_def(path_book)', filename=r"thisprofileoutput")
            
#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(ABSOLUTE_LOGGING_PATH)
    logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)

    for arg in sys.argv:
        print(arg)
    
    #curr_dir = os.path.dirname(os.path.realpath(__file__))
    #path_book = os.path.abspath(curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary.xlsx')
    #print("Profile")
    #this_profile = cProfile.run('run_project_def(path_book)', filename=r"thisprofileoutput")

#     #flgp = 1
#     
#     if flgp == 2:
#         path_evolog = r'c:\ExportDir\\test_log.txt'
#         pop, stats = main(path_db,path_evolog)
#         pop.sort(key=lambda x: x.fitness.values)
#         
#         print(stats)
#     
#         with open(r"../../examples/ga/pareto_front/zdt1_front.json") as optimal_front_data:
#             optimal_front = json.load(optimal_front_data)
#         # Use 500 of the 1000 points in the json file
#         optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))
#         print("Convergence: ", convergence(pop, optimal_front))
#         print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))
#         
#         print_res(pop,optimal_front)




    #myLogger = logging.getLogger()
    #myLogger.setLevel("DEBUG")

    #logging.debug("Started _main".format())
    
    #print FREELANCE_DIR
    
    #unittest.main()

    #logging.debug("Finished _main".format())
