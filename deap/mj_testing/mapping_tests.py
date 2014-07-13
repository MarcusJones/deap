#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function

from config import *

import logging.config
import unittest

from utility_inspect import whoami, whosdaddy, listObject

# Testing imports
from deap.design_space import Variable, DesignSpace, Mapping, ObjectiveSpace, Individual2, Objective
from deap.design_space import generate_ORM_individual,generate_individuals_table,convert_individual_DB

from deap import creator, base
import sqlalchemy as sa
import utility_SQL_alchemy as util_sa

from UtilityLogger import loggerCritical
from deap.mj_utilities.db_base import DB_Base
import deap as dp

#===============================================================================
# Logging
#===============================================================================
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#===============================================================================
# Unit testing
#===============================================================================

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
        
        
        print(type(test_ind[0]), test_ind[0])
    
    def test020_DSpace(self):
        pass
        #test_ind = Individual2([0.1,0.2],[1,2],["AA","B"],[0,1],["Cost","Size"])
        #print(test_ind)
        #print(test_ind[2])

class MappingBasicTests(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(whoami())
        myLogger.setLevel("CRITICAL")
        
        NDIM = 3
        BOUND_LOW, BOUND_UP = 0.0, 1.0
        BOUND_LOW_STR, BOUND_UP_STR = '0.0', '.2'
        RES_STR = '0.10'
       
        # Create DSpace
        basis_variables = list()
        for i in range(NDIM):
            basis_variables.append(Variable.from_range("{}".format(i), 'float', BOUND_LOW_STR, RES_STR, BOUND_UP_STR))
        

        thisDspace = DesignSpace(basis_variables)
        self.D1 = thisDspace
        
        # Create OSpace
        obj1 = Objective('obj1', 'Max')
        obj2 = Objective('obj2', 'Min')
        objs = [obj1, obj2]
        self.obj_space1 = ObjectiveSpace(objs)

        myLogger.setLevel("DEBUG")

    def test010_SimpleCreation(self):
        print("**** TEST {} ****".format(whoami()))
        
        this_mapping = Mapping(self.D1, self.obj_space1)
        
        creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
        
        this_mapping.assign_individual(Individual2)
        this_mapping.assign_fitness(creator.FitnessMin)
        
        print(this_mapping)
        print("Design space; {}".format(this_mapping.design_space))
        print("Fitness; {}".format(this_mapping.fitness))
        print("Individual class; {}".format(this_mapping.Individual))
        print("First variable; {}".format(this_mapping.design_space.basis_set[0]))
        
        print(this_mapping.get_random_mapping())



class MappingPopulationTests(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(whoami())
        myLogger.setLevel("CRITICAL")
        
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
        
        creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
        
        self.mapping.assign_individual(Individual2)
        self.mapping.assign_fitness(creator.FitnessMin)
        
        myLogger.setLevel("DEBUG")

    def test010_get_pop(self):
        print("**** TEST {} ****".format(whoami()))
        print(self.mapping)
        with loggerCritical():
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
        
        creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
        
        self.mapping.assign_individual(Individual2)
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
            


class TestMate(unittest.TestCase):
    def setUp(self):
        #print "**** TEST {} ****".format(whoami())
        #myLogger.setLevel("CRITICAL")
        
        #=======================================================================
        # Parameters
        #=======================================================================
        NDIM = 3
        BOUND_LOW, BOUND_UP = 0.0, 1.0
        BOUND_LOW_STR, BOUND_UP_STR = '0.0', '.2'
        RES_STR = '0.10'
        
        #=======================================================================
        # Create DB
        #=======================================================================
        self.engine = sa.create_engine('sqlite:///:memory:', echo=0)
        #engine = sa.create_engine('sqlite:///{}'.format(self.path_new_sql), echo=self.ECHO_ON)
        Session = sa.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        logging.debug("Initialized session {} with SQL alchemy version: {}".format(self.engine, sa.__version__))
       
        #=======================================================================
        # Create mapping
        #=======================================================================
        # Variables
        basis_variables = list()
        for i in range(NDIM):
            basis_variables.append(Variable.from_range("{}".format(i), 'float', BOUND_LOW_STR, RES_STR, BOUND_UP_STR))
        for var in basis_variables:
            self.session.add_all(var.variable_tuple)    # DB ADD vectors        
        
        self.session.add_all(basis_variables)   # DB ADD variables
            
        # DSpace
        thisDspace = DesignSpace(basis_variables)
        D1 = thisDspace
        
        # OSpace
        obj1 = Objective('obj1', 'Max')
        obj2 = Objective('obj2', 'Min')
        objs = [obj1, obj2]
        obj_space1 = ObjectiveSpace(objs)
        for obj in objs:
            self.session.add(obj)   # DB ADD
        
        # Mapping
        self.mapping = Mapping(D1, obj_space1)
        creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
        self.mapping.assign_individual(Individual2)
        self.mapping.assign_fitness(creator.FitnessMin)
        
        #=======================================================================
        # Results is composed of a class and a table, mapped together        
        #=======================================================================
        res_ORM_table = generate_individuals_table(self.mapping)
        self.Results = generate_ORM_individual(self.mapping)
        sa.orm.mapper(self.Results, res_ORM_table) 
        
        # 
        DB_Base.metadata.create_all(self.engine)    
        self.session.commit() 
        
        myLogger.setLevel("DEBUG")

    def test010_mate(self):
        print("**** TEST {} ****".format(whoami()))
        pop = self.mapping.get_random_population(20)
        toolbox = dp.base.Toolbox()

        from deap.benchmarks import mj as mj
        toolbox.register("evaluate", mj.mj_zdt1_decimal)
    
        util_sa.print_all_pretty_tables(self.engine)
        
        
        eval_count = 0
        final_pop = list()
        #with loggerCritical():
        # Only evaluate each individual ONCE
        for ind in pop:
            
            # First, check if in DB
            try:
                query = self.session.query(self.Results).filter(self.Results.hash == ind.hash)
                ind = query.one()
                logging.debug("Retrieved {}".format(ind))
                
            # Otherwise, do a fresh evaluation
            except sa.orm.exc.NoResultFound:
                ind = toolbox.evaluate(ind)
                logging.debug("Evaluated {}".format(ind))
                eval_count += 1
                res = convert_individual_DB(self.Results,ind)
                self.session.add(res)
            final_pop.append(ind)
        
        logging.debug("Evaluated population size {}, of which are {} new ".format(len(pop), eval_count))
        self.session.commit()
        logging.debug("Committed {} new individuals to DB".format(eval_count))


                    
            