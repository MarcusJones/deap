#===============================================================================
# Set up
#===============================================================================
#--- Import settings
from __future__ import division
from __future__ import print_function

from utility_inspect import whoami, whosdaddy, listObject
import unittest
from deap.mj_config.deapconfig import *
import logging.config

logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#--- Import other
import numpy as np
import json
import matplotlib.pyplot as plt


#--- Import design space
from deap.design_space import Variable, DesignSpace, Mapping, ObjectiveSpace
from deap.design_space import Individual2

#--- Import deap
import random
from deap.mj_evaluators.zdt1_exe import evaluate
import array
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence
from deap import creator
from deap import tools


#===============================================================================
# Unit testing
#===============================================================================

class test1(unittest.TestCase):
    def setUp(self):
        pass

        
    def test010_(self):
        print("**** TEST {} ****".format(whoami()))
        NDIM = 30
        BOUND_LOW, BOUND_UP = 0.0, 1.0
        BOUND_LOW_STR, BOUND_UP_STR = '0.0', '1.0' 
        RES_STR = '0.01'
        NGEN = 250
        POPSIZE = 40
        MU = 100
        CXPB = 0.9
        
        # Create variables
        var_names = [str(num) for num in range(NDIM)]
        myLogger.setLevel("CRITICAL")
        basis_set = [Variable.from_range(name, BOUND_LOW_STR, RES_STR, BOUND_UP_STR) for name in var_names]
        myLogger.setLevel("DEBUG")
        
        # Create DSpace
        thisDspace = DesignSpace(basis_set)
        
        # Create OSpace
        objective_names = ('obj1','obj3')
        objective_goals = ('Max', 'Min')
        this_obj_space = ObjectiveSpace(objective_names, objective_goals)
        mapping = Mapping(thisDspace, this_obj_space)
                
        # Statistics and logging
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)        
        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "std", "min", "avg", "max"
        
        creator.create("FitnessMin", base.fitness, weights=(-1.0, -1.0))
        
        toolbox = base.Toolbox()
        
        #--- Eval
        toolbox.register("evaluate", benchmarks.mj_zdt1_decimal)
        
        #--- Operators
        toolbox.register("mate", tools.cxSimulatedBinaryBounded, 
                         low=BOUND_LOW, up=BOUND_UP, eta=20.0)
        toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, 
                         eta=20.0, indpb=1.0/NDIM)
        toolbox.register("select", tools.selNSGA2)
        
        # Create the population
        mapping.assign_individual(Individual2)
        mapping.assign_fitness(creator.FitnessMin)
        pop = mapping.get_random_population(POPSIZE)
        
        # Evaluate first pop        
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]
        toolbox.map(toolbox.evaluate, invalid_ind)
        logging.debug("Evaluated {} individuals".format(len(invalid_ind)))
        
        # Check that they are evaluated
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]
        assert not invalid_ind
        
        pop = toolbox.select(pop, len(pop))
        logging.debug("Crowding distance applied to initial population of {}".format(len(pop)))
        
        myLogger.setLevel("CRITICAL")
        for gen in range(1, NGEN):
            # Vary the population
            offspring = tools.selTournamentDCD(pop, len(pop))
            offspring = [toolbox.clone(ind) for ind in offspring]
            logging.debug("Selected and cloned {} offspring".format(len(offspring)))
            
            #print([ind.__hash__() for ind in offspring])
            #for ind in offspring:
            #    print()
            pairs = zip(offspring[::2], offspring[1::2])
            for ind1, ind2 in pairs:
                if random.random() <= CXPB:
                    toolbox.mate(ind1, ind2)
                    
                toolbox.mutate(ind1)
                toolbox.mutate(ind2)
                del ind1.fitness.values, ind2.fitness.values
            logging.debug("Operated over {} pairs".format(len(pairs)))

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            processed_ind = toolbox.map(toolbox.evaluate, invalid_ind)
            logging.debug("Evaluated {} individuals".format(len(processed_ind)))
            
            #raise
            #for ind, fit in zip(invalid_ind, fitnesses):
            #    ind.fitness.values = fit
        
            # Select the next generation population
            pop = toolbox.select(pop + offspring, MU)
            record = stats.compile(pop)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)
            print(logbook.stream)
        
        ###
        with open(r"C:\Users\jon\git\deap1\examples\ga\pareto_front\zdt1_front.json") as optimal_front_data:
            optimal_front = json.load(optimal_front_data)
        # Use 500 of the 1000 points in the json file
        optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))
                
        pop.sort(key=lambda x: x.fitness.values)
        print(stats)
        print("Convergence: ", convergence(pop, optimal_front))
        print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))

        
        front = np.array([ind.fitness.values for ind in pop])
        optimal_front = np.array(optimal_front)
        plt.scatter(optimal_front[:,0], optimal_front[:,1], c="r")
        print(front)
        plt.scatter(front[:,0], front[:,1], c="b")
        plt.axis("tight")
        #plt.savefig('C:\ExportDir\test1.png')
        plt.savefig('C:\\ExportDir\\out.pdf', transparent=True, bbox_inches='tight', pad_inches=0)
        #plt.show()
        

#             