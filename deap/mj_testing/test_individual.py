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
from deap.design_space import Variable, DesignSpace, Mapping, ObjectiveSpace, Objective
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
from sqlalchemy.orm.exc import MultipleResultsFound,NoResultFound


#---
class Basic(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(whoami())
        pass

    def test010_simple1(self):
        print("**** TEST {} ****".format(whoami()))
        test_ind = Individual2([0.1,0.2],[1,2],["AA","B"],['float','float'],[0,1],["Cost","Size"])
        print(test_ind)
        print(test_ind[0])
        test_ind[1] = 2
        print(test_ind)
        self.assertRaises(IndexError, lambda: test_ind[2])
        #print()
    
    
    def test020_DSpace(self):
        test_ind = Individual2([0.1,0.2],[1,2],["AA","B"],[0,1],["Cost","Size"])
        print(test_ind)
        #print(test_ind[2])


def main(seed=None):

    engine = sa.create_engine('sqlite:///:memory:', echo=0)
    #engine = sa.create_engine('sqlite:///{}'.format(self.path_new_sql), echo=self.ECHO_ON)
    Session = sa.orm.sessionmaker(bind=engine)
    session = Session()
    logging.debug("Initialized session {} with SQL alchemy version: {}".format(engine, sa.__version__))
    #value_list, names, indices, fitness, fitness_names
    #test_ind = Individual2([0.1,0.2])



    
    

    #===========================================================================
    # Parameters
    #===========================================================================
    NDIM = 3
    BOUND_LOW, BOUND_UP = 0.0, 1.0
    BOUND_LOW_STR, BOUND_UP_STR = '0.0', '.2'
    RES_STR = '0.10'
    NGEN = 10
    POPSIZE = 8
    MU = 100
    CXPB = 0.9
    range(NDIM)

    #===========================================================================
    # Variables and design space
    #===========================================================================
    # Create basis set
    var_names = ['var'+'a'*(num+1) for num in range(NDIM)]
    #myLogger.setLevel("CRITICAL")
    with loggerCritical():
        basis_set = [Variable.from_range(name, BOUND_LOW_STR, RES_STR, BOUND_UP_STR) for name in var_names]
    #myLogger.setLevel("DEBUG")

    # Add to DB
    #DB_Base.metadata.create_all(engine)
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

    #===========================================================================
    # Mapping and results table
    #===========================================================================
    mapping = Mapping(thisDspace, this_obj_space)
    results_table = mapping.generate_individuals_table(DB_Base.metadata)
    sa.orm.mapper(Individual2, results_table)
    


    #print(results_table)
    #for at in dir(results_table):
    #    print(at)
    #raise
    
    #===========================================================================
    # Flush DB
    #===========================================================================
    DB_Base.metadata.create_all(engine)
    session.commit()
    #util_sa.print_all_pretty_tables(engine, 20)

    #raise
    #===========================================================================
    # Statistics and logging
    #===========================================================================
    creator.create("FitnessMin", base.fitness, weights=(-1.0, -1.0))

    #===========================================================================
    # Create the population
    #===========================================================================
    mapping.assign_individual(Individual2)
    mapping.assign_fitness(creator.FitnessMin)
    ind = mapping.get_random_mapping()
    
    raise
    print(ind)
    print(dir(ind))
    print(ind[0])

if __name__ == "__main__":

    main()
