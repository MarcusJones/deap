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
#--- Import settings
from __future__ import division
from __future__ import print_function

from utility_inspect import whoami, whosdaddy, listObject
import unittest
from deap.mj_config.deapconfig import *
import logging.config

logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
#myLogger = logging.getLogger('sqlalchemy.engine')
#myLogger.setLevel("DEBUG")
myLogger.setLevel("DEBUG")
from UtilityLogger import loggerCritical

#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

#--- Import other
import numpy as np
import json
import matplotlib.pyplot as plt
#from math import sqrt
import utility_SQL_alchemy as util_sa
#--- Import design space
from deap.design_space import Variable, DesignSpace, Mapping, ObjectiveSpace, Objective, Individual2
from deap.design_space import generate_individuals_table,generate_ORM_individual,convert_individual_DB, convert_DB_individual
from deap.mj_utilities.db_base import DB_Base
from deap.benchmarks import mj as mj
from deap.benchmarks.old_init import zdt1
#--- Import deap
import random
from deap.mj_evaluators.zdt1_exe import evaluate
import array
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence
from deap import creator
from deap import algorithms
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence
from deap import creator
from deap import tools


import sqlalchemy as sa
import utility_SQL_alchemy as util_sa
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.exc import MultipleResultsFound,NoResultFound


#---
#def 

def printpop(msg,pop):
    print('*****************', msg)
    for ind in pop:
        print(ind)


def main(seed=None):

    engine = sa.create_engine('sqlite:///:memory:', echo=0)
    #engine = sa.create_engine('sqlite:///{}'.format(self.path_new_sql), echo=self.ECHO_ON)
    Session = sa.orm.sessionmaker(bind=engine)
    session = Session()
    logging.debug("Initialized session {} with SQL alchemy version: {}".format(engine, sa.__version__))

    #===========================================================================
    # Statistics
    #===========================================================================
    stats = tools.Statistics(lambda ind: ind.Fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"
    

    
    #===========================================================================
    # Parameters
    #===========================================================================
    NDIM = 30
    BOUND_LOW, BOUND_UP = 0.0, 1.0
    BOUND_LOW_STR, BOUND_UP_STR = '0.0', '1.0'
    RES_STR = '0.001'
    NGEN = 100
    POPSIZE = 4*2
    MU = 100
    CXPB = 0.9

    #===========================================================================
    # Variables and design space
    #===========================================================================
    # Create basis set
    var_names = ['var'+'a'*(num+1) for num in range(NDIM)]    
    with loggerCritical():
        basis_set = [Variable.from_range(name, 'float', BOUND_LOW_STR, RES_STR, BOUND_UP_STR) for name in var_names]
    
    # Add to DB
    for var in basis_set:
        session.add_all(var.variable_tuple)
        
    # Add the variable names to the DB
    session.add_all(basis_set)

    # Create DSpace
    thisDspace = DesignSpace(basis_set)

    #===========================================================================
    # Objectives
    #===========================================================================
    # Create OSpace
    obj1 = Objective('obj1', 'Max')
    obj2 = Objective('obj2', 'Min')
    objs = [obj1, obj2]
    this_obj_space = ObjectiveSpace(objs)
    
    # Add to DB
    for obj in objs:
        session.add(obj)
        
    #=======================================================================
    # Results is composed of a class and a table, mapped together        
    #=======================================================================
    mapping = Mapping(thisDspace, this_obj_space)
    res_ORM_table = generate_individuals_table(mapping)
    Results = generate_ORM_individual(mapping)
    sa.orm.mapper(Results, res_ORM_table) 
    
    #===========================================================================
    # Flush DB
    #===========================================================================
    DB_Base.metadata.create_all(engine)    
    session.commit()
    #util_sa.print_all_pretty_tables(engine, 20)

    #===========================================================================
    # Fitness
    #===========================================================================
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0), names = mapping.objective_space.objective_names)
    
    toolbox = base.Toolbox()

    #===========================================================================
    # Eval
    #===========================================================================
    #toolbox.register("evaluate", old_init.mj_zdt1_decimal)
    toolbox.register("evaluate", mj.mj_zdt1_decimal)

    #===========================================================================
    # Operators
    #===========================================================================
    toolbox.register("mate", tools.mj_string_cxSimulatedBinaryBounded,
                     low=BOUND_LOW, up=BOUND_UP, eta=20.0)    
    #toolbox.register("mate", tools.cxSimulatedBinaryBounded,
    #                 low=BOUND_LOW, up=BOUND_UP, eta=20.0)
    toolbox.register("mutate", tools.mj_string_mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP,
                     eta=20.0, indpb=1.0/NDIM)
    toolbox.register("select", tools.mj_selNSGA2)

    #===========================================================================
    # Create the population
    #===========================================================================
    mapping.assign_individual(Individual2)
    mapping.assign_fitness(creator.FitnessMin)
    pop = mapping.get_random_population(POPSIZE)
    #print(pop[0])
    #print(pop[0].vara)
    #raise
    #===========================================================================
    # Flush DB
    #===========================================================================
    #print(pop)
    DB_Base.metadata.create_all(engine)    
    #session.add_all(pop)
    session.commit()

    #===========================================================================
    # Evaluate first pop
    #===========================================================================
    eval_count = 0
    
    final_pop = list()
    with loggerCritical():
        # Only evaluate each individual ONCE
        for ind in pop:
            
            # First, check if in DB
            try:
                query = session.query(Results).filter(Results.hash == ind.hash)
                res = query.one()
                ind = convert_DB_individual(res, mapping)
                #final_pop.append(ind)
                logging.debug("Retrieved {}".format(ind))
                
            # Otherwise, do a fresh evaluation
            except sa.orm.exc.NoResultFound:
                ind = toolbox.evaluate(ind)
                logging.debug("Evaluated {}".format(ind))
                eval_count += 1
                res = convert_individual_DB(Results,ind)
                session.add(res)
            final_pop.append(ind)
    
    logging.debug("Evaluated population size {}, of which are {} new ".format(len(pop), eval_count))
    session.commit()
    logging.debug("Committed {} new individuals to DB".format(eval_count))

    # Assert that they are indeed evaluated
    for ind in final_pop:
        assert ind.Fitness.valid, "{}".format(ind)
        
    # And re-copy
    pop = final_pop
    
    #===========================================================================
    # Selection
    #===========================================================================
    pop = toolbox.select(pop, len(pop))

    logging.debug("Crowding distance applied to initial population of {}".format(len(pop)))
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
        
        #=======================================================================
        # Mate and mutate
        #=======================================================================
        pairs = zip(offspring[::2], offspring[1::2])
        for ind1, ind2 in pairs:
            if random.random() <= CXPB:
                toolbox.mate(ind1, ind2)
            
            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.Fitness.values, ind2.Fitness.values
        #logging.debug("Operated over {} pairs".format(len(pairs)))

        #=======================================================================
        # Evaluate the individuals
        #=======================================================================
        eval_offspring = list()
        eval_count = 0
        retrieval_count = 0
        with loggerCritical():
            for ind in offspring:
                
                # First, check if in DB
                try:
                    query = session.query(Results).filter(Results.hash == ind.hash)
                    res = query.one()
                    ind = convert_DB_individual(res, mapping)
                    #eval_offspring.append(ind)
                    #logging.debug("Retrieved {}".format(ind))
                    retrieval_count += 1
                # Otherwise, do a fresh evaluation
                except sa.orm.exc.NoResultFound:
                    ind = toolbox.evaluate(ind)
                    #logging.debug("Evaluated {}".format(ind))
                    eval_count += 1
                    res = convert_individual_DB(Results,ind)
                    session.add(res)
                    
                eval_offspring.append(ind)
        #logging.debug("Retrieved {}, Evaluated {}".format(retrieval_count,eval_count))

        session.commit()

        combined_pop = pop + eval_offspring

        
        #printpop('Parents',pop)
        
        # Select the next generation population
        pop = toolbox.select(combined_pop, MU)
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=eval_count, **record)
        print(logbook.stream)
        
        

    util_sa.print_all_pretty_tables(engine, 20000)

    return pop, stats

def showconvergence(pop):
    pop.sort(key=lambda x: x.Fitness.values)
    with open(r"../../examples/ga/pareto_front/zdt1_front.json") as optimal_front_data:
        optimal_front = json.load(optimal_front_data)
        
    # Use 500 of the 1000 points in the json file
    optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))


    pop.sort(key=lambda x: x.Fitness.values)

    print("Convergence: ", convergence(pop, optimal_front))
    print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))
    
    
if __name__ == "__main__":

    import cProfile
    path_profile  = r"C:\\ExportDir\testprofile.txt"
    #cProfile.run('main()', filename=path_profile)
    

    pop, stats = main()
    #showconvergence(pop)
    #print(stats)


