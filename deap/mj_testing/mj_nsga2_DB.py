#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.
#===============================================================================
# Import settings and logger
#===============================================================================
from __future__ import division
from __future__ import print_function
from deap.mj_config.deapconfig import *

import logging.config
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")
from UtilityLogger import loggerCritical

import deap.mj_utilities.util_db_process as util_dbproc


#===============================================================================
# Utilities
#===============================================================================
from deap.mj_utilities.util_graphics import print_res
import utility_SQL_alchemy as util_sa
from deap.mj_utilities.db_base import DB_Base
import deap.mj_utilities.db_base
import utility_path as util_path
#===============================================================================
# Import other
#===============================================================================
import numpy as np
import json
import sqlalchemy as sa

#===============================================================================
# Import design space
#===============================================================================
#from deap.design_space import Variable, DesignSpace, Mapping, ObjectiveSpace, Objective, Individual2
#from deap.design_space import generate_individuals_table,generate_ORM_individual,convert_individual_DB, convert_DB_individual
import deap.design_space as ds

from deap.benchmarks import mj as mj
#from deap.benchmarks.old_init import zdt1

#===============================================================================
# Import deap
#===============================================================================
import random
from deap.benchmarks.tools import diversity, convergence
from deap import base
from deap import creator
from deap import tools





def printpop(msg, pop):
    print('*****************', msg)
    for ind in pop:
        print(ind)
        
def printhashes(pop, msg=""):
    hash_list = [ind.hash for ind in pop]
    print("{:>20} - {}".format(msg,sorted(hash_list)))
  
def evaluate_pop(pop,session,Results,mapping,toolbox):
    #printhashes(pop,"First pop")
    
    eval_count = 0
    final_pop = list()
    with loggerCritical():
        # Only evaluate each individual ONCE
        for ind in pop:
            # First, check if in DB
            try:
                
                #print(Results.hash)
                #print(ind.hash)
                query = session.query(Results).filter(Results.hash == ind.hash)
                
                #print(query)
                res = query.one()
                #res = 
                ind = ds.convert_DB_individual(res, mapping)
                logging.debug("Retrieved {}".format(ind))
                
            # Otherwise, do a fresh evaluation
            except sa.orm.exc.NoResultFound:
                ind = toolbox.evaluate(ind)
                logging.debug("Evaluated {}".format(ind))
                eval_count += 1
                res = ds.convert_individual_DB(Results,ind)
                session.add(res)
                session.commit()    
                
            final_pop.append(ind)
    

            
    #logging.debug("Evaluated population size {}, of which are {} new ".format(len(pop), eval_count))
    
    #session.commit()
    #logging.debug("Committed {} new individuals to DB".format(eval_count))
    
    # Assert that they are indeed evaluated
    for ind in final_pop:
        assert ind.fitness.valid, "{}".format(ind)
        
    return final_pop, eval_count
    
def main(path_db, seed=None):
    #===========================================================================
    #---Database
    #===========================================================================
    engine = sa.create_engine("sqlite:///{}".format(path_db), echo=0, listeners=[util_sa.ForeignKeysListener()])
    #engine = sa.create_engine("mysql:///{}".format(path_db), echo=0,listeners=[util_sa.ForeignKeysListener()])
    #engine = sa.create_engine('sqlite:///{}'.format(self.path_new_sql), echo=self.ECHO_ON)
    Session = sa.orm.sessionmaker(bind=engine)
    session = Session()
    logging.debug("Initialized session {} with SQL alchemy version: {}".format(engine, sa.__version__))

    #===========================================================================
    # Statistics
    #===========================================================================
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"
    
    #===========================================================================
    #---Parameters
    #===========================================================================
    NDIM = 30
    BOUND_LOW_STR, BOUND_UP_STR = '0.0', '1.0'
    #RES_STR = '0.002'
    RES_STR = '0.01'
    NGEN = 250
    POPSIZE = 4*10
    #MU = 100
    CXPB = 0.9
    PROB_CX = 0.1
    JUMPSIZE = 10
    toolbox = base.Toolbox()
    
    #===========================================================================
    # Algorithm
    #===========================================================================
    toolbox.register("evaluate", mj.mj_zdt1_decimal)
    toolbox.register("mate", tools.mj_list_flip, indpb = PROB_CX)
    toolbox.register("mutate", tools.mj_random_jump, jumpsize=JUMPSIZE,indpb=1.0/NDIM)
    toolbox.register("select", tools.selNSGA2)
    
    #===========================================================================
    # Variables and design space
    #===========================================================================
    # Create basis set
    var_names = ['var{}'.format(num) for num in range(NDIM)]    
    with loggerCritical():
        basis_set = [ds.Variable.from_range(name, 'float', BOUND_LOW_STR, RES_STR, BOUND_UP_STR) for name in var_names]
    
    # Add to DB
    for var in basis_set:
        session.add_all(var.variable_tuple)
        
    # Add the variable names to the DB
    session.add_all(basis_set)

    # Create DSpace
    thisDspace = ds.DesignSpace(basis_set)


    #===========================================================================
    #---Objectives
    #===========================================================================
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0), names = ('obj1', 'obj2'))
        
    # Create OSpace from Fitness
    objs = list()
    for name,weight in zip(creator.FitnessMin.names,creator.FitnessMin.weights):
        objs.append(ds.Objective(name,weight))
    this_obj_space = ds.ObjectiveSpace(objs)
    session.add_all(objs)    
        
    #=======================================================================
    #---Mapping
    # Results is composed of a class and a table, mapped together        
    #=======================================================================
    mapping = ds.Mapping(thisDspace, this_obj_space)
    res_ORM_table = ds.generate_individuals_table(mapping)
    Results = ds.generate_ORM_individual(mapping)
    sa.orm.mapper(Results, res_ORM_table) 

    DB_Base.metadata.create_all(engine)
    #session.commit()
    #util_sa.print_all_pretty_tables(engine, 20000)
    
    #raise
    
    #===========================================================================
    # First generation    
    #===========================================================================
    
    #---Create the population
    mapping.assign_individual(ds.Individual2)
    mapping.assign_fitness(creator.FitnessMin)
    pop = mapping.get_random_population(POPSIZE)


    #---Evaluate first pop
    path_excel_out = r"C:\ExportDir\test_before.xlsx"

    #util_sa.print_all_excel(engine,path_excel_out, loggerCritical())
    DB_Base.metadata.create_all(engine)
    session.commit()
    #raise    
    pop,eval_count = evaluate_pop(pop,session,Results,mapping,toolbox)
    
    # Add generations
    gen_rows = [ds.Generation(0,ind.hash) for ind in pop]
    session.add_all(gen_rows)
    
    # Selection
    pop = toolbox.select(pop, len(pop))
    logging.debug("Crowding distance applied to initial population of {}".format(len(pop)))
    
    session.commit()

    record = stats.compile(pop)
    logbook.record(gen=0, evals=eval_count, **record)
    print(logbook.stream)

    for gen in range(1, NGEN):

        #=======================================================================
        # Select the population
        #=======================================================================
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [mapping.clone_ind(ind) for ind in offspring]
        #logging.debug("Selected and cloned {} offspring".format(len(offspring)))
        
        #printpop('Offspring',pop)
        
        #printhashes(offspring,"Cloned offspring g{}".format(gen))

        #=======================================================================
        # Mate and mutate
        #=======================================================================
        varied_offspring = list()
        pairs = zip(offspring[::2], offspring[1::2])
        for ind1, ind2 in pairs:
            if random.random() <= CXPB:
                toolbox.mate(ind1, ind2)
            
            ind1 = toolbox.mutate(ind1)
            ind2 = toolbox.mutate(ind2)
            toolbox.mutate(ind1)
            toolbox.mutate(ind2)            
            del ind1.fitness.values, ind2.fitness.values
            
            varied_offspring.extend([ind1,ind2])
        #logging.debug("Operated over {} pairs".format(len(pairs)))
        #printhashes(varied_offspring,"Varied offspring g{}".format(gen))
        
        #=======================================================================
        # Evaluate the individuals
        #=======================================================================
        eval_offspring = list()
        #eval_count = 0
        #retrieval_count = 0

        eval_offspring,eval_count = evaluate_pop(pop,session,Results,mapping,toolbox)
        
        # Add generations
        #gen_rows = [ds.Generation(gen,ind.hash) for ind in pop]
        #session.add_all(gen_rows)        

        combined_pop = pop + eval_offspring
        
        # Select the next generation population
        pop = toolbox.select(combined_pop, POPSIZE)
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=eval_count, **record)
        print(logbook.stream)
        
        #=======================================================================
        # Add this generation
        #=======================================================================
        gen_rows = [ds.Generation(gen,ind.hash) for ind in pop]
        session.add_all(gen_rows)
        session.commit() 

    util_sa.printOnePrettyTable(engine, 'Results',maxRows = None)
    util_sa.printOnePrettyTable(engine, 'Generations',maxRows = None)
    #engine,metadata
    #this_frame = util_sa.get_frame_simple(engine,'Results')
    path_excel_out = r"C:\ExportDir\test.xlsx"
    util_sa.print_all_excel(engine,path_excel_out, loggerCritical())
    #print(this_frame)
    
    #Generations.join(Results)
    qry = session.query(Results,ds.Generation)
    qry = qry.join(ds.Generation)
    print(qry)
    print(qry.all())
    #print("{} individuals seen".format(len(hash_list)))
    #print("{} individuals unique".format(len(set(hash_list))))
    return pop, stats

def showconvergence(pop):
    pop.sort(key=lambda x: x.fitness.values)
    with open(r"../../examples/ga/pareto_front/zdt1_front.json") as optimal_front_data:
        optimal_front = json.load(optimal_front_data)
        
    # Use 500 of the 1000 points in the json file
    optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))


    pop.sort(key=lambda x: x.fitness.values)
    
    print("Convergence: ", convergence(pop, optimal_front))
    print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))
    



if __name__ == "__main__":

    import cProfile
    path_profile  = r"C:\\ExportDir\testprofile.txt"
    #cProfile.run('main()', filename=path_profile)
    

    with open(r"../../examples/ga/pareto_front/zdt1_front.json") as optimal_front_data:
        optimal_front = json.load(optimal_front_data)
    # Use 500 of the 1000 points in the json file
    optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))
    
    path_db = r':memory:'
    path_db = r"C:\ExportDir\DB\test.sql"
    util_path.check_path(path_db)
    
    
    pop, stats = main(path_db)
    pop.sort(key=lambda x: x.fitness.values)
    
    print(stats)
    print("Convergence: ", convergence(pop, optimal_front))
    print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))
    
    
    print_res(pop,optimal_front)


