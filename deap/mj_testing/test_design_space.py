#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function
import unittest

# Utilities
#from config import *
from ExergyUtilities.utility_inspect import get_self
from ExergyUtilities.utility_logger import LoggerCritical, LOGGING_CONFIG_2

# Logging
import logging
logging.basicConfig(format=LOGGING_CONFIG_2, level=logging.DEBUG, datefmt='%I:%M:%S')
my_logger = logging.getLogger()
my_logger.setLevel("DEBUG")

# Own
#from deap import design_space
import deap.design_space as ds
#import deap.mj_utilities.util_db_process as util_proc
# from deap.mj_utilities.db_base import DB_Base

# DEAP
import deap as dp

#===============================================================================
# Testing
#===============================================================================
class TestDesignSpace(unittest.TestCase):
    def setUp(self):
        pass

    def test010_get_pop(self):
        print("**** TEST {} ****".format(get_self()))
        
        NDIM = 3
        BOUND_LOW, BOUND_UP = 0.0, 1.0
        BOUND_LOW_STR, BOUND_UP_STR = '0.0', '.2'
        RES_STR = '0.10'
       
        # Create DSpace
        basis_variables = list()
        for i in range(NDIM):
            basis_variables.append(ds.Variable.from_range("{}".format(i), 'float', BOUND_LOW_STR, RES_STR, BOUND_UP_STR))

        thisDspace = ds.DesignSpace(basis_variables)
        D1 = thisDspace
        
        # Create OSpace
        obj1 = ds.Objective('obj1', 'Max')
        obj2 = ds.Objective('obj2', 'Min')
        objs = [obj1, obj2]
        obj_space1 = ds.ObjectiveSpace(objs)

        # Mapping
        mapping = ds.Mapping(D1, obj_space1)

        # Fitness
        fitness = dp.creator.create("Fitness", dp.base.Fitness, weights=(-1.0, -1.0), names = ('obj1', 'obj2'))
        mapping.assign_fitness(dp.creator.Fitness)

        #print(mapping.design_space.individual)
        raise
        mapping.assign_individual()
        mapping.get_random_population(20)
        
        print(mapping.individual)
        
        # Creator
        print(mapping)
        print(mapping.fitness)
        #print(mapping.)
        raise

        
        mapping.assign_fitness(fitness)
        #mapping.assign_individual(ds.Individual)
        #mapping.assign_evaluator(algorithm['life_cycle'])
        #mapping.get_random_mapping(flg_verbose=True)
        
        #mapping.get_global_search()
        
        #creator.create("FitnessMin", base.fitness, weights=(-1.0, -1.0))
        
        #self.mapping.assign_individual(Individual)
        #self.mapping.assign_fitness(creator.FitnessMin)
        
        #my_logger.setLevel("DEBUG")


class MappingPopulationTests(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(whoami())
        my_logger.setLevel("CRITICAL")
        
        NDIM = 3
        BOUND_LOW, BOUND_UP = 0.0, 1.0
        BOUND_LOW_STR, BOUND_UP_STR = '0.0', '.2'
        RES_STR = '0.10'
       
        # Create DSpace
        basis_variables = list()
        for i in range(NDIM):
            basis_variables.append(Variable.from_range("{}".format(i), 'float', BOUND_LOW_STR, RES_STR, BOUND_UP_STR))
        

        thisDspace = DesignSpace(basis_variables)
        D1 = thisDspace
        
        # Create OSpace
        obj1 = Objective('obj1', 'Max')
        obj2 = Objective('obj2', 'Min')
        objs = [obj1, obj2]
        obj_space1 = ObjectiveSpace(objs)

        self.mapping = Mapping(D1, obj_space1)
        
        creator.create("FitnessMin", base.fitness, weights=(-1.0, -1.0))
        
        self.mapping.assign_individual(Individual)
        self.mapping.assign_fitness(creator.FitnessMin)
        
        my_logger.setLevel("DEBUG")

    def test010_get_pop(self):
        print("**** TEST {} ****".format(whoami()))
        print(self.mapping)
        with LoggerCritical():
            pop = self.mapping.get_random_population(20)
            
        print(pop)
        print(pop[0])
        print()
        print(type(pop[0][0]),pop[0][0])
        this_ind = self.mapping.get_random_mapping()
        print(this_ind)
        print()
        print(type(this_ind[0]),this_ind[0])

class MappingPopulationTests2(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(whoami())
        myLogger.setLevel("CRITICAL")

        self.engine = sa.create_engine('sqlite:///:memory:', echo=0)
        #engine = sa.create_engine('sqlite:///{}'.format(self.path_new_sql), echo=self.ECHO_ON)
        Session = sa.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        logging.debug("Initialized session {} with SQL alchemy version: {}".format(self.engine, sa.__version__))
        
        NDIM = 3
        BOUND_LOW, BOUND_UP = 0.0, 1.0
        BOUND_LOW_STR, BOUND_UP_STR = '0.0', '.2'
        RES_STR = '0.10'
       
        # Create DSpace
        basis_variables = list()
        for i in range(NDIM):
            basis_variables.append(Variable.from_range("{}".format(i), 'float', BOUND_LOW_STR, RES_STR, BOUND_UP_STR))
        for var in basis_variables:
            self.session.add_all(var.variable_tuple)        

        thisDspace = DesignSpace(basis_variables)
        D1 = thisDspace
        
        # Create OSpace
        obj1 = Objective('obj1', 'Max')
        obj2 = Objective('obj2', 'Min')
        objs = [obj1, obj2]
        obj_space1 = ObjectiveSpace(objs)
        for obj in objs:
            self.session.add(obj)
            
        self.mapping = Mapping(D1, obj_space1)
        
        creator.create("FitnessMin", base.fitness, weights=(-1.0, -1.0))
        
        self.mapping.assign_individual(Individual)
        self.mapping.assign_fitness(creator.FitnessMin)

        myLogger.setLevel("DEBUG")
        
        DB_Base.metadata.create_all(self.engine)    
        self.session.add_all(basis_variables)        
        self.session.commit()


    def test020_send_pop_DB(self):
        print("**** TEST {} ****".format(whoami()))
        #print(self.mapping)
        res_ORM_table = generate_individuals_table(self.mapping)
        #print(res_ORM_table)

        Results = generate_ORM_individual(self.mapping)
        #print(Results)
        
        sa.orm.mapper(Results, res_ORM_table) 

        DB_Base.metadata.create_all(self.engine)    
        self.session.commit() 
        
        with loggerCritical():
            pop = self.mapping.get_random_population(50)

        results = [convert_individual_DB(Results,ind) for ind in set(pop)]

        self.session.add_all(results)
        self.session.commit()

        #util_sa.print_all_pretty_tables(self.engine)
        
        #print(type(self.mapping.design_space.basis_set[0]))
        
        #raise
        #self.mapping.design_space.basis_set
        
        val_classes = [var.ValueClass for var in self.mapping.design_space.basis_set]
        qry = self.session.query(Results, *val_classes)
        for var in self.mapping.design_space.basis_set:
            #print("J")
            qry = qry.join(var.ValueClass)
        
        print(type(qry))
        
        for res, v1, v2, v3 in qry.all():
            print(res)
            #print(res[0])
            #print(type(res))
            #print(dir(res))
            #print(dir(res))
            #print(res.var_c_0)
            #raise
            #print(res)
            



class DesignSpaceBasicTests(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(get_self())
        myLogger.setLevel("CRITICAL")
        print("Setup")
        myLogger.setLevel("DEBUG")

    def test010_SimpleCreation(self):
        print("**** TEST {} ****".format(get_self()))
        
