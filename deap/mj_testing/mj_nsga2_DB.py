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
from UtilityLogger import loggerCritical,loggerDebug

import deap.mj_utilities.util_db_process as util_dbproc


#===============================================================================
# Utilities
#===============================================================================
from deap.mj_utilities.util_graphics import print_res
import utility_SQL_alchemy as util_sa
from deap.mj_utilities.db_base import DB_Base
import deap.mj_utilities.db_base
import utility_path as util_path
import cProfile
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


def assert_valid(pop):
    for ind in pop:
        assert ind.fitness.valid, "{}".format(ind)

def get_results_hashes(session,Results):
   # metadata = sa.MetaData()
    #metadata.reflect(engine)    
    #return metadata
    #results_table = meta.tables["Results"]
    #meta = sa.MetaData()
    #meta.reflect(engine)
    #results_table = meta.tables["Results"]
    #qry = sa.select(results_table.c.hash)
    #res = engine.execute(qry).fetchall()
    #print(res)
    
    
    hashes = [row[0] for row in session.query(Results.hash).all()]
    return(hashes)
    
    

           
def assert_subset(pop1, pop2):
    pop1_hashes = set([ind.hash for ind in pop1])
    pop2_hashes = set([ind.hash for ind in pop2])
    assert(pop1_hashes <= pop2_hashes)



def printpoplist(pop, msg=None):
    hashes = [ind.hash for ind in pop]
    hashes.sort()
    
    print("{:20} {}".format(msg,hashes))
    pass

def get_gen_evo_dict_entry(pop):
    hashes = [ind.hash for ind in pop]
    hashes.sort()
    return(hashes)

def printpop(msg, pop):
    print('*****************', msg)
    for ind in pop:
        print(ind)
        
        
def print_gen_dict(gd,gennum):
    print("Generation {}".format(gennum))
    
    print("{:17} {}".format('Start population',gd['Start population']))
    #print("{:17} {}".format('Population',gd['Population']))
    print("{:17} {}".format('Parents',gd['Selected parents']))
    print("{:17} {}".format('Mated offspring',gd['Mated offspring']))
    print("{:17} {}".format('Mutated offspring',gd['Mutated offspring']))
    print("{:17} {}".format('Combined',gd['Combined']))
    print("{:17} {}".format('Next',gd['Next population']))

def printhashes(pop, msg=""):
    hash_list = [ind.hash for ind in pop]
    print("{:>20} - {}".format(msg,sorted(hash_list)))
  
def evaluate_pop(pop,session,Results,mapping,toolbox):
    """evaluate_pop() performs a filter to ensure that each individual is only evaluated ONCE during the entire evolution
    evaluate_pop calls toolbox.evaluate(individual)
    - Entire population will be stored in final_pop list
    - If individual is already in DB, it is moved immediately into final_pop (recreated by ORM)
    - If not in DB, the individual is evaluated and stored in a dictionary newly_evald and added to final_pop
    - DUPLICATE HANDLING: If the individual is already existing in newly_evald, it is not re-evaluated, but added directly to final_pop
    - final_pop is returned by function
    """
    logging.debug("EVALUATE population size {}: {}".format(len(pop),sorted([i.hash for i in pop])))
    eval_count = 0
    
    final_pop = list()
    eval_pop = list()
    
    pop_ids = [ind.hash for ind in pop]
    
    # Get all matching from DB
    qry = session.query(Results).filter(Results.hash.in_(( pop_ids )))
    res = qry.all()
    
    # Assemble results into a dict
    results_dict = dict()
    for r in res:
        this_ind = ds.convert_DB_individual(r,mapping)
        results_dict[r.hash] = this_ind
    
    while pop:
        this_ind = pop.pop()
        try: 
            this_ind = results_dict[this_ind.hash]
            final_pop.append(this_ind)
        except KeyError:
            eval_pop.append(this_ind)
    
    for ind in final_pop:
        if not ind.fitness.valid:
            print(ind)
            util_sa.printOnePrettyTable(session.bind, 'Results',maxRows = None)
            raise Exception("Invalid fitness from DB")
        #assert ind.fitness.valid, "{}".format(ind)
                
    logging.debug("EVALUATE {} individuals are already in database: {}".format(len(results_dict),sorted([i.hash for i in final_pop])))
    logging.debug("EVALUATE {} individuals are to be evaluated: {}".format(len(eval_pop),sorted([i.hash for i in eval_pop])))
    
    
    with loggerDebug():
        # Only evaluate each individual ONCE
        newly_evald = dict()
        while eval_pop:
            ind = eval_pop.pop()
            
            # Check if it has been recently evaluated
            try: 
                logging.debug("Recently evaluated: {} ".format(newly_evald[ind.hash]))
                copy_ind = newly_evald[ind.hash]
                assert(copy_ind.fitness.valid)
                final_pop.append(copy_ind)
                # Skip to next 
                continue
            except KeyError:
                # This individual needs to be evaluated
                #pass
            
                # Do a fresh evaluation
                #with loggerCritical():
                with loggerCritical():
                    ind = toolbox.evaluate(ind)
                    logging.debug("Newly evaluated {}".format(ind.hash))
                assert(ind.fitness.valid)
                eval_count += 1
                res = ds.convert_individual_DB(Results,ind)
                newly_evald[res.hash] = ind
                session.merge(res)
                final_pop.append(ind)
    session.commit()

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

    # Results
    path_excel_out = r"C:\ExportDir\test_before.xlsx"


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
    RES_STR = '0.001'
    NGEN = 250
    POPSIZE = 4*5
    P_CX_THIS_PAIR = 0.5
    P_CX_THESE_ALLELES = 0.1
    JUMPSIZE = 100
    toolbox = base.Toolbox()
    
    #===========================================================================
    #---Algorithm
    #===========================================================================
    toolbox.register("evaluate", mj.mj_zdt1_decimal)
    toolbox.register("mate", tools.mj_list_flip, indpb = P_CX_THESE_ALLELES)
    toolbox.register("mutate", tools.mj_random_jump, jumpsize=JUMPSIZE,indpb=1.0/NDIM)
    toolbox.register("select", tools.selNSGA2)
    
    #===========================================================================
    #---Variables and design space
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
    session.commit()
    #util_sa.print_all_pretty_tables(engine, 20000)

    #===========================================================================
    # First generation    
    #===========================================================================
    #---Create the population
    mapping.assign_individual(ds.Individual2)
    mapping.assign_fitness(creator.FitnessMin)
    pop = mapping.get_random_population(POPSIZE)



    DB_Base.metadata.create_all(engine)
    session.commit()

    #---Evaluate first pop
    print("* GENERATION {:>5} ************************".format(0))

    #raise    
    pop, eval_count = evaluate_pop(pop,session,Results,mapping,toolbox)

    #printpoplist(pop, 'First eval')

    # Add generations
    gen_rows = [ds.Generation(0,ind.hash) for ind in pop]
    session.add_all(gen_rows)
    
    # Selection
    toolbox.select(pop, len(pop))
    
    #printpoplist(pop,'First selection')

    logging.debug("Crowding distance applied to initial population of {}".format(len(pop)))
    
    session.commit()


    record = stats.compile(pop)
    logbook.record(gen=0, evals=eval_count, **record)
    print(logbook.stream)

    #---Start evolution
    for gen in range(1, NGEN):
        this_gen_evo = dict()
        print("* GENERATION {:>5} ************************".format(gen))
        
        this_gen_evo['Start population'] = get_gen_evo_dict_entry(pop)
        
        #=======================================================================
        #--- Select the parents
        #=======================================================================
        logging.debug("Selecting generation {}".format(gen))
        parents = tools.selTournamentDCD(pop, len(pop))
        cloned_parents = [ind.clone() for ind in parents]

        this_gen_evo['Selected parents'] = get_gen_evo_dict_entry(parents)

        
        #=======================================================================
        #--- Crossover
        #=======================================================================
        logging.debug("Varying generation {}".format(gen))
        
        
        pairs = zip(cloned_parents[::2], cloned_parents[1::2])
        
        with loggerCritical():
            offspring = list()
            for ind1, ind2 in pairs:
                if random.random() <= P_CX_THIS_PAIR and ind1.hash != ind2.hash:
                    ind1,ind2 = toolbox.mate(ind1, ind2)
                    
                offspring.extend([ind1,ind2])

        this_gen_evo['Mated offspring'] = get_gen_evo_dict_entry(offspring)
        

        for ind in offspring:
            del ind.fitness.values

        #=======================================================================
        #--- Mutate
        #=======================================================================
        with loggerCritical():
            mutated_offspring = list()
            for ind in offspring:
                ind = toolbox.mutate(ind)
                mutated_offspring.append(ind)
                

        for ind in mutated_offspring:
            del ind.fitness.values

        this_gen_evo['Mutated offspring'] = get_gen_evo_dict_entry(mutated_offspring)
            
        #=======================================================================
        #--- Evaluate the individuals
        #=======================================================================
        logging.debug("Evaluating generation {}".format(gen))
        #eval_offspring = list()
        cloned_offspring = [ind.clone() for ind in mutated_offspring]
        eval_offspring, eval_count = evaluate_pop(cloned_offspring,session,Results,mapping,toolbox)

        for ind in parents:
            assert ind.fitness.valid, "{}".format(ind)
        for ind in eval_offspring:
            assert ind.fitness.valid, "{}".format(ind)
        

        #=======================================================================
        #--- Select the next generation population
        #=======================================================================
        combined_pop = parents + eval_offspring

        assert_subset(combined_pop, parents + eval_offspring)
        
        assert(len(combined_pop) == len(parents) + len(eval_offspring))
        #assert(set(combined_pop) <= set(parents).union(set(eval_offspring)))
        
        for ind in combined_pop:
            assert(ind in parents or ind in eval_offspring)
        
        this_gen_evo['Combined'] = get_gen_evo_dict_entry(combined_pop)
                
        for ind in combined_pop:
            assert ind.fitness.valid, "{}".format(ind)
                
        pop = toolbox.select(combined_pop, POPSIZE)
        
        this_gen_evo['Next population'] = get_gen_evo_dict_entry(pop)
        
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=eval_count, **record)
        print(logbook.stream)

        #=======================================================================
        # Add this generation
        #=======================================================================
        population_hashes = [ind.hash for ind in pop]

        gen_rows = [ds.Generation(gen,this_hash) for this_hash in population_hashes]
        
        combined_pop_hashes = [ind.hash for ind in combined_pop]
        assert(set(population_hashes) <= set(combined_pop_hashes))

        
        #util_sa.printOnePrettyTable(engine, 'Results', maxRows = None)
        
        print_gen_dict(this_gen_evo,gen)
        
        session.add_all(gen_rows)
        session.commit()
        
        #pop = [ind.clone() for ind in new_pop]
        
        

    #---Finished generation
        
    #util_sa.printOnePrettyTable(engine, 'Results',maxRows = None)
    #util_sa.printOnePrettyTable(engine, 'Generations',maxRows = None)
    
    path_excel_out = r"C:\ExportDir\test.xlsx"
    #util_sa.print_all_excel(engine,path_excel_out, loggerCritical())
    
    #Generations.join(Results)
    #qry = session.query(Results,ds.Generation)
    #qry = qry.join(ds.Generation)
    #print(qry)
    #print(qry.all())
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
    path_db = r':memory:'
    path_db = r"C:\ExportDir\DB\test.sql"
    util_path.check_path(path_db)
    path_profile  = r"C:\\ExportDir\testprofile.txt"
    
    flgp = 2
    
    if flgp == 1:
        cProfile.run('main(path_db)', filename=path_profile)
    
    if flgp == 2:
        
        pop, stats = main(path_db)
        pop.sort(key=lambda x: x.fitness.values)
        
        print(stats)
    
        with open(r"../../examples/ga/pareto_front/zdt1_front.json") as optimal_front_data:
            optimal_front = json.load(optimal_front_data)
        # Use 500 of the 1000 points in the json file
        optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))
        print("Convergence: ", convergence(pop, optimal_front))
        print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))
        
        print_res(pop,optimal_front)


