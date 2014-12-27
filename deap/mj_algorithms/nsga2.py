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

import logging

from UtilityLogger import loggerCritical,loggerDebug

#===============================================================================
# Utilities
#===============================================================================
import deap.mj_utilities.util_db_process as util_dbproc
from deap.mj_utilities.util_graphics import print_res
import ExergyUtilities.utility_SQL_alchemy as util_sa 
from deap.mj_utilities.db_base import DB_Base
import deap.mj_utilities.util_general as util


import ExergyUtilities.utility_path as util_path

#===============================================================================
# Standard
#===============================================================================
import time
import cProfile

#===============================================================================
# Import other
#===============================================================================
import numpy as np
import json
import sqlalchemy as sa
from decimal import Decimal

#===============================================================================
# Import design space
#===============================================================================
from deap import design_space as ds

#===============================================================================
# Import deap
#===============================================================================
import random
from deap.benchmarks.tools import diversity, convergence
from deap import base
from deap import creator
from deap import tools

#===============================================================================
# Code
#===============================================================================

def nsga2(settings, algorithm, parameters, operators, mapping, session, Results):
    with open(settings['path_evolog'], 'w+') as evolog:
        print("Start log", file=evolog)

    engine = session.bind
    
    last_gen = session.query(ds.Generation).order_by(ds.Generation.id.desc()).first()
    
    
    #---Retrieve a population
    if last_gen:
        logging.debug("Last generation found in DB: {}".format(last_gen.gen))        
        start_gennum = last_gen.gen
        #print(start_gennum)
        individual_hashes = session.query(ds.Generation.individual).filter(ds.Generation.gen == start_gennum).all()
        individual_hashes = [ind_hash[0] for ind_hash in individual_hashes]
        pop = list()
        for ind_hash in individual_hashes:
            result = session.query(Results).filter(Results.hash == ind_hash).one()
            this_chromosome = list()
            for var in mapping.design_space.basis_set:
                
                index = getattr(result, "var_c_{}".format(var.name))
                var.index = index - 1
                this_chromosome.append(var.return_allele())

            fit_vals = list()
            for name in mapping.objective_space.objective_names:
                fit= getattr(result, "obj_c_{}".format(name))
                fit_vals.append(fit)

            this_individual = ds.individual(this_chromosome,mapping.fitness())
            this_individual.fitness.setValues(fit_vals)
            #print(this_individual)
            pop.append(this_individual)
        logging.debug("Retrieved {} individuals from generation {}".format(len(pop),start_gennum))
        
    else: 
        
        #===========================================================================
        # First generation    
        #===========================================================================
        logging.debug("Initializing new population".format())
        
        pop = mapping.get_random_population(parameters['Population size'])
    
        DB_Base.metadata.create_all(engine)
        session.commit()
        start_gennum = 0
    
        
    #---Evaluate first pop
    print("* GENERATION {:>5} ************************".format(start_gennum))
    
    pop, eval_count =  util.evaluate_pop(pop,session,Results,mapping,settings)
    #algorithm['evaluator'](pop,session,Results,mapping,settings)
    
    #pop, eval_count = util.evaluate_pop(pop,session,Results,mapping,algorithm['evaluate'],settings)
    
    gen_rows = [ds.Generation(start_gennum,ind_hash.hash) for ind_hash in pop]
    session.add_all(gen_rows)
    
    # Selection
    logging.debug("Selecting next generation {}".format(algorithm['select'].__name__))
    
    algorithm['select'](pop, len(pop))
    
    logging.debug("Crowding distance applied to initial population of {}".format(len(pop)))
    
    session.commit()

    #---Start evolution
    for gen in range(start_gennum+1, start_gennum + parameters['Generations']):
        
        t_gen_start = time.time()

        print("* GENERATION {:>5} ************************".format(gen))
        with open(settings['path_evolog'], 'a') as evolog:
            print("* GENERATION {:>5} ************************".format(gen), file=evolog)
            
        this_gen_evo = dict()
        
        crowds = [ind_hash.fitness.crowding_dist for ind_hash in pop]
        crowds.sort()
        print("Mean crowding: {} Crowding distances {}".format(np.mean(crowds),crowds))
        
        this_gen_evo['Start population'] = util.get_gen_evo_dict_entry(pop)
        
        #=======================================================================
        #--- Select the parents
        #=======================================================================
        logging.debug("Selecting generation {}".format(gen))
        parents = operators['select'](pop, len(pop))
        cloned_parents = [ind_hash.clone() for ind_hash in parents]

        this_gen_evo['Selected parents'] = util.get_gen_evo_dict_entry(parents)
        
        #=======================================================================
        #--- Crossover
        #=======================================================================
        logging.debug("Varying generation {}".format(gen))
        t_cx_start  = time.time() 
        pairs = zip(cloned_parents[::2], cloned_parents[1::2])
        
        with loggerCritical():
            offspring = list()
            for ind1, ind2 in pairs:
                if random.random() <= parameters['Probability crossover individual'] and ind1.hash != ind2.hash:
                    ind1,ind2 = operators['mate'](ind1, ind2,
                                                  mapping = mapping ,
                                                  parameters = parameters,
                                                  path_evolog = settings['path_evolog'])
                    
                offspring.extend([ind1,ind2])
                
        
        this_gen_evo['Mated offspring'] = util.get_gen_evo_dict_entry(offspring)
        logging.debug("Crossover complete".format())
        
        t_cx_elapsed = time.time() - t_cx_start 
        logging.debug("Crossover time {:0.2} seconds".format(t_cx_elapsed))

        #=======================================================================
        #--- Mutate
        #=======================================================================
        t_mu_start = time.time()
        #with loggerCritical():
        with loggerDebug():
            mutated_offspring = list()
            for ind_hash in offspring:
                if random.random() <= parameters['Probability mutation individual']:
                    ind_hash = operators['mutate'](ind_hash,
                                              mapping = mapping,
                                              parameters = parameters,
                                              path_evolog = settings['path_evolog'])
                mutated_offspring.append(ind_hash)
        this_gen_evo['Mutated offspring'] = util.get_gen_evo_dict_entry(mutated_offspring)
        logging.debug("Mutation complete".format())
        
        t_mu_elapsed = time.time() - t_mu_start 
        logging.debug("Mutation time {:0.2} seconds".format(t_mu_elapsed))
            
        #=======================================================================
        #--- Evaluate the individual_hashes
        #=======================================================================
        t_eval_start = time.time()
        logging.debug("Evaluating generation {}".format(gen))
        cloned_offspring = [ind_hash.clone() for ind_hash in mutated_offspring]
        eval_offspring, eval_count = util.evaluate_pop(cloned_offspring,session,Results,mapping,settings)
        
        for ind_hash in parents:
            assert ind_hash.fitness.valid, "{}".format(ind_hash)
        for ind_hash in eval_offspring:
            assert ind_hash.fitness.valid, "{}".format(ind_hash)
        t_eval_elapsed = time.time() - t_eval_start 
        logging.debug("Evaluation time {:0.3} seconds".format(t_eval_elapsed))
            
        #=======================================================================
        #--- Select the next generation population
        #=======================================================================
        combined_pop = parents + eval_offspring

        util.assert_subset(combined_pop, parents + eval_offspring)
        
        assert(len(combined_pop) == len(parents) + len(eval_offspring))
        #assert(set(combined_pop) <= set(parents).union(set(eval_offspring)))
        
        for ind_hash in combined_pop:
            assert(ind_hash in parents or ind_hash in eval_offspring)
        
        this_gen_evo['Combined'] = util.get_gen_evo_dict_entry(combined_pop)
                
        for ind_hash in combined_pop:
            assert ind_hash.fitness.valid, "{}".format(ind_hash)
                
        pop = algorithm['select'](combined_pop, parameters['Population size'])
        
        this_gen_evo['Next population'] = util.get_gen_evo_dict_entry(pop)

        #=======================================================================
        # Add this generation
        #=======================================================================
        population_hashes = [ind_hash.hash for ind_hash in pop]

        gen_rows = [ds.Generation(gen,this_hash) for this_hash in population_hashes]
        
        combined_pop_hashes = [ind_hash.hash for ind_hash in combined_pop]
        assert(set(population_hashes) <= set(combined_pop_hashes))

        
        #util_sa.printOnePrettyTable(engine, 'Results', maxRows = None)
        
        util.print_gen_dict(this_gen_evo,gen,settings['path_evolog'])
        
        session.add_all(gen_rows)
        session.commit()

        t_gen_end = time.time()
        elapsed = t_gen_end - t_gen_start 
        logging.debug("Generation {} completed after {:0.2} seconds".format(gen,elapsed))
    
    #---Finished generation

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
        path_evolog = r'c:\ExportDir\\test_log.txt'
        pop, stats = main(path_db,path_evolog)
        pop.sort(key=lambda x: x.fitness.values)
        
        print(stats)
    
        with open(r"../../examples/ga/pareto_front/zdt1_front.json") as optimal_front_data:
            optimal_front = json.load(optimal_front_data)
        # Use 500 of the 1000 points in the json file
        optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))
        print("Convergence: ", convergence(pop, optimal_front))
        print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))
        
        print_res(pop,optimal_front)


