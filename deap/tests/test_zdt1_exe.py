#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function

from deap.mj_config.deapconfig import *

import logging.config
import unittest

import numpy as np

from utility_inspect import whoami, whosdaddy, listObject

from deap.design_space import Variable, DesignSpace, Mapping, ObjectiveSpace


from deap.mj_evaluators.zdt1_exe import evaluate
import array
#from deap import algorithms
from deap import base
from deap import benchmarks
#from deap.benchmarks.tools import diversity, convergence
from deap import creator
from deap import tools

#===============================================================================
# Logging
#===============================================================================
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#===============================================================================
# Unit testing
#===============================================================================

class test1(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(whoami())
        #myLogger.setLevel("CRITICAL")
        self.NDIM = 30
        self.BOUND_LOW, self.BOUND_UP = '0.0', '1.0' 
        RES = '0.01'

        var_names = [str(num) for num in range(self.NDIM)]
        
        basis_set = [Variable.from_range(name, self.BOUND_LOW, RES, self.BOUND_UP) for name in var_names]
        # Create DSpace
        thisDspace = DesignSpace(basis_set)
        
        # Create OSpace
        objective_names = ('obj1','obj3')
        objective_goals = ('Max', 'Min')
        this_obj_space = ObjectiveSpace(objective_names, objective_goals)
        obj_space1 = this_obj_space
        
        #myLogger.setLevel("DEBUG")
        
        
    def test010_(self):
        print("**** TEST {} ****".format(whoami()))
        #evaluate()
        creator.create("FitnessMin", base.FitnessMJ, weights=(-1.0, -1.0))
        
        toolbox = base.Toolbox()
        
        
        toolbox.register("evaluate", benchmarks.zdt1)

        toolbox.register("mate", tools.cxSimulatedBinaryBounded, 
                         low=self.BOUND_LOW, up=self.BOUND_UP, eta=20.0)
                         
        toolbox.register("mutate", tools.mutPolynomialBounded, low=self.BOUND_LOW, up=self.BOUND_UP, 
                         eta=20.0, indpb=1.0/self.NDIM)
        
        toolbox.register("select", tools.selNSGA2)
        #Individual2
        #creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin)
        
        
        #self.this_mapping = Mapping(self.D1, self.obj_space1, BasicIndividual, random_fitness)
        
