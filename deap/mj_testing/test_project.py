"""This is a testing module
"""

#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function
import os
import unittest

# Logging
import logging
logging.basicConfig(format='%(funcName)-20s %(levelno)-3s: %(message)s', level=logging.DEBUG, datefmt='%I:%M:%S')
my_logger = logging.getLogger()
my_logger.setLevel("DEBUG")

# External 
#import xxx

# Own
from ExergyUtilities.utility_inspect import get_self, get_parent
from deap.mj_projects import run_proj 

#===============================================================================
# Unit testing
#===============================================================================

class allTests(unittest.TestCase):

    def setUp(self):
        print("**** TEST {} ****".format(get_self()))
        self.curr_dir = os.path.dirname(os.path.realpath(__file__))
        
    def test000_empty(self):
        print("**** TEST {} ****".format(get_self()))
 
    def test010_testing_zdt1(self):
        print("**** TEST {} ****".format(get_self()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\testing_zdt1.xlsx')
        run_proj.run_project_def(path_book)
        
    def test020_nsga1_zdt1_Xbinary_Mbinary(self):
        print("**** TEST {} ****".format(get_self()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary.xlsx')
        run_proj.run_project_def(path_book)

    def test021_nsga1_zdt1_Xbinary_Mbinary_SMALL(self):
        print("**** TEST {} ****".format(get_self()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary SMALL.xlsx')
        run_proj.run_project_def(path_book)

    def test030_nsga1_zdt1_Xbinary_Mbinary_EXE(self):
        print("**** TEST {} ****".format(get_self()))
        path_book = os.path.abspath(self.curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary_EXE.xlsx')
        run_proj.run_project_def(path_book)
    
    def test040_run_multiple_in_dir(self):
        print("**** TEST {} ****".format(get_self()))
        #raise  
    
        #multiple_path = r"D:\Projects\PhDprojects\Multiple"
        #multiple_path = r"D:\Projects\PhDprojects\Multiple\this_test"
        multiple_path = r'D:\Projects\PhDprojects\Multiple\ExplorationStudy2\\'
        #rootPath, search_name, search_ext
        def_book_paths = util_path.get_files_by_name_ext(multiple_path,'.','xlsx')
        for path_book in def_book_paths:
            time.sleep(2)
            print("RUNNING", path_book)
            run_project_def(path_book)
            #path_sql
        #print(files)


    
    def test100_Postprocess(self):
        print("**** TEST {} ****".format(get_self()))
        path_sql = r"D:\Projects\PhDprojects\testZDT1exe\Run168\SQL\results.sql"
        path_mlab = r"D:\Projects\PhDprojects\testZDT1exe\Run168\Matlab"
        util_proc.process_db_to_mat(path_sql,path_mlab)
        
#     def test200_parameterize_excel(self):
#         path_template = r'D:\Projects\PhDprojects\Multiple\Template1.xlsx'
#         path_target_dir = r'D:\Projects\PhDprojects\Multiple\this_test\\'
#         parameterize_excel_def(path_template,path_target_dir)

    def test210_parameterize_excel_table_version(self):
        path_template = r'D:\Projects\PhDprojects\Multiple\template nsga1_zdt1_Xbinary_Mbinary.xlsx'
        path_target_dir = r'D:\Projects\PhDprojects\Multiple\ExplorationStudy2\\'
        
        #=======================================================================
        # Possible values of parameters
        #=======================================================================
        mods = list()
        mods.append(['Parameters', 'Population size', [20,40, 80]])
        mods.append(['Parameters', 'Generations', [250]])

        mods.append(['Parameters', 'Probability crossover individual', [0,0.5,1]])
        mods.append(['Parameters', 'Probability crossover allele', [0, 0.03, 0.1, 0.5]])
        
        mods.append(['Parameters', 'Probability mutation individual', [0, 0.5, 1]])
        mods.append(['Parameters', 'Probability mutation allele', [0, 0.03, 0.1, 0.5]])
        
        mods.append(['Parameters', 'Crowding degree', [10,20,40]])
        
        #=======================================================================
        # Each variant expanded
        #=======================================================================
        expanded_mods = list()
        for m in mods:
            expanded_mods.append(([[m[0], m[1], val] for val in m[2]]))
            #print(m)
        #raise
        #=======================================================================
        # Cartesian product
        #=======================================================================
        res = itertools.product(*expanded_mods)
        
        final_defs = list()
        for r in res:
            #print(r) 
            final_defs.append(r)
        
        mod_dicts = list()
        for row in final_defs:
            #print(row)
            #raise
            changes = list()
            for change in row:
                this_dict = dict(zip(['Sheet', 'Parameter', 'Value'],change))
                #print(this_dict)
                #raise
                changes.append(this_dict)
            mod_dicts.append(changes)
            
        print('Raw parameter vectors',len(mod_dicts))
        # Remove all cases where 
        for row in mod_dicts:
            for change in row:
                #print(change)
                if change['Parameter'] == 'Probability crossover individual' and change['Value'] == 0:
                    for change in row:                    
                        if change['Parameter'] == 'Probability crossover allele' and change['Value'] != 0:
                            mod_dicts.remove(row)
                            
                if change['Parameter'] == 'Probability mutation individual' and change['Value'] == 0:
                    for change in row:                    
                        if change['Parameter'] == 'Probability mutation allele' and change['Value'] != 0:
                            try:
                                mod_dicts.remove(row)
                            except:
                                pass                            
                    #print(change)
        print('After removal',len(mod_dicts))                    
        
        parameterize_excel_def_from_dicts(path_template,path_target_dir,mod_dicts)
        
        #parameterize_excel_def_from_table(path_template,path_target_dir,final_defs)



        
    def test300_Profile(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        path_book = os.path.abspath(curr_dir + r'\definitionbooks\nsga1_zdt1_Xbinary_Mbinary.xlsx')
        print("Profile")
        cProfile.run('run_project_def(path_book)', filename=r"thisprofileoutput")
     
     

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
