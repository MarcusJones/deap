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
myLogger.setLevel("DEBUG")

#--- Import other
import numpy as np
import json
import matplotlib.pyplot as plt
#from math import sqrt
import utility_SQL_alchemy as util_sa
#--- Import design space
from deap.design_space import Variable, DesignSpace, Mapping, ObjectiveSpace
from deap.design_space import Individual2
from deap.mj_utilities.db_base import DB_Base

#--- Import deap
import random
from deap.mj_evaluators.zdt1_exe import evaluate
import array
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence
from deap import creator
from deap import tools


from deap import algorithms
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence
from deap import creator
from deap import tools

import sqlalchemy as sa
import utility_SQL_alchemy as util_sa
from sqlalchemy import Column, Integer, String


#---

def main(seed=None):

    engine = sa.create_engine('sqlite:///:memory:', echo=True)
    #engine = sa.create_engine('sqlite:///{}'.format(self.path_new_sql), echo=self.ECHO_ON)
    Session = sa.orm.sessionmaker(bind=engine)
    session = Session()
    logging.debug("Initialized session {} with SQL alchemy version: {}".format(engine, sa.__version__))


    NDIM = 3
    BOUND_LOW, BOUND_UP = 0.0, 1.0
    BOUND_LOW_STR, BOUND_UP_STR = '0.0', '1.0'
    RES_STR = '0.01'
    NGEN = 10
    POPSIZE = 8
    MU = 100
    CXPB = 0.9
    range(NDIM)

    # Create variables
    var_names = ['var'+'a'*(num+1) for num in range(NDIM)]
    myLogger.setLevel("CRITICAL")
    basis_set = [Variable.from_range(name, BOUND_LOW_STR, RES_STR, BOUND_UP_STR) for name in var_names]
    myLogger.setLevel("DEBUG")
    # Add variables to DB

    DB_Base.metadata.create_all(engine)
    session.add_all(basis_set)



    # Create DSpace
    thisDspace = DesignSpace(basis_set)


    # Create OSpace
    objective_names = ('obj1','obj3')
    objective_goals = ('Max', 'Min')
    this_obj_space = ObjectiveSpace(objective_names, objective_goals)
    mapping = Mapping(thisDspace, this_obj_space)
    #print(mapping.design_space.basis_set[0].variable_tuple[0].__table__)
    #raise
    #print(session.dirty)
    #print(session.new)

    session.commit()
    util_sa.print_all_pretty_tables(engine, 20)
    #print(DB_Base.metadata.tables.keys())
    raise


    # Statistics and logging
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)
    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))

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

if __name__ == "__main__":
    with open(r"../../examples/ga/pareto_front/zdt1_front.json") as optimal_front_data:
        optimal_front = json.load(optimal_front_data)
    # Use 500 of the 1000 points in the json file
    optimal_front = sorted(optimal_front[i] for i in range(0, len(optimal_front), 2))

    pop, stats = main()
    pop.sort(key=lambda x: x.fitness.values)

    print(stats)
    print("Convergence: ", convergence(pop, optimal_front))
    print("Diversity: ", diversity(pop, optimal_front[0], optimal_front[-1]))
