#===============================================================================
# Title of this Module
# Authors; MJones, Other
# 00 - 2012FEB05 - First commit
# 01 - 2012MAR17 - Update to ...
# 02 - 2012JUN15 - Major overhaul of all code, simplification
#===============================================================================

"""This module does stuff
Etc.
"""

#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function

# Setup
from deap.mj_config.deapconfig import *
import logging.config

# Standard library
from decimal import Decimal
import random
import time
import itertools
import sys
import imp

# External library
import numpy as np


# Utilites
import sqlalchemy as sa
import utility_SQL_alchemy as util_sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table


from deap.mj_utilities.db_base import DB_Base

#===============================================================================
# Logging
#===============================================================================
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")

#===============================================================================
# Code
#===============================================================================
#--- Utilities
def convert_settings(table_rows):
    settings = dict()
    for row in table_rows:
        settings[row['attribute']] = row['description']
    return settings

def empty_fitness(objectiveNames):
    """Utility to initialize the objective vector to NULL
    """
    return [[name, None] for name in objectiveNames]


def generate_chromosome(basis_set):
    """Simple utility to order the values and names
    """
    variable_names = tuple([var.name for var in  basis_set])
    variable_indices = tuple([var.index for var in  basis_set])
    variableValues = tuple([var.value for var in basis_set])

    return zip(variable_names,variable_indices,variableValues)

#---

def evaluate_population(population, engine):
    """Given a list of individuals, evaluate only those which are
    1. Unique
    2. Not already existing in database
    """
    logging.info("Evaluating {} individuals, typical: {}".format(len(population),population[0]))

    unique_pop = list(set(population))
    logging.info("Of these {} individuals, {} are unique".format(len(population),len(unique_pop)))

    # Get metadata
    metadata = sa.MetaData()
    metadata.reflect(engine)

    # Get all tables
    #util_sa.print_all_pretty_tables(engine)
    results_table =  metadata.tables['results']
    objectives_table = metadata.tables['objectives']

    # Get objective names
    #objectives_table.fetchall()
    objective_names = util_sa.get_rows(engine,objectives_table)
    objective_names = [row[1] for row in objective_names]
    #logging.info("Objectives: {}".format(objective_names))

    objective_columns = [results_table.c[obj_name] for obj_name in objective_names]

    # Here the population is filtered into 2:
    # 1. The already-evaluated list
    evaluated_pop = list()
    # 2. The pending list
    pending_pop = list()

    # DO for all in population
    while unique_pop:
        indiv = unique_pop.pop()

        # First, go into the results table and select this individual
        qry = results_table.select(results_table.c.hash ==  indiv.__hash__())
        res = engine.execute(qry).fetchall()


        if not res:
            # This is a new individual, needs evaluation
            pending_pop.append(indiv)

        else:
            # This individual has already been evaluated
            # This should return exactly one row
            assert(len(res) == 1)
            row = res[0]

            # Select and assign the fitness rows for this individual
            objectives = [row[col] for col in objective_columns]
            indiv.fitness = zip(objective_names,objectives)

            evaluated_pop.append(indiv)

    logging.info("Of these {} unique individuals, {} are new, {} are existing".format(len(pending_pop)+len(evaluated_pop), len(pending_pop),len(evaluated_pop)))

    # Run all the pending individuals, append onto evaluated_pop
    for indiv in pending_pop:
        indiv = indiv.evaluate()
        evaluated_pop.append(indiv)

    # Now re-expand the population including clones
    final_pop = list()
    for indiv in population:
        # This individual MUST have been evaluated now, either newly or existing
        assert(indiv in evaluated_pop)

        # Get this individual from the evaluated set
        index = evaluated_pop.index(indiv)
        final_pop.append(evaluated_pop[index])

    # Return this generation back for addition into DB
    # add_population_db also checks first for duplicates before adding them to results
    # The generation number will be automatically added based on last gen number
    return final_pop

#--- Objects

class Mapping(object):
    def __init__(self, design_space, objective_space):
        self.design_space = design_space
        self.objective_space = objective_space
        #self.individual = individual
        #self.evaluator = evaluator

        logging.info(self)
    #, generating {} instances


    def __str__(self):
        return "Mapping dimension {} domain to dimension {} range".format(self.design_space.dimension,
                                                                  self.objective_space.dimension)


    def assign_individual(self, Individual):
        self.Individual = Individual
        logging.info("This mapping will produce individuals of class {}".format(Individual.__name__))

    def assign_fitness(self, fitness):
        self.fitness = fitness
        logging.info("This mapping will produce fitness of class {}".format(fitness.__name__))

    #--- Database
    def generate_individuals_table(self, metadata):
        columns = list()
        columns.append(sa.Column('hash', sa.Integer, primary_key=True))
        columns.append(sa.Column('start', sa.DateTime))
        columns.append(sa.Column('finish', sa.DateTime))    
        for var in self.design_space.basis_set:
            columns.append(sa.Column("{}".format(var.name), sa.Integer, sa.ForeignKey('vector_{}.id'.format(var.name)), nullable = False,  ))
        for obj in self.objective_space.objective_names:
            columns.append(sa.Column("{}".format(obj), sa.Float, nullable = False,  ))
            columns.append(sa.Column("{}".format(obj), sa.Float))
        
        tab_results = sa.Table('results', metadata, *columns)
        
        return(tab_results)  


    # Generating points in the space-------------
    def get_random_mapping(self):
        """
        Randomly sample all basis_set vectors, return a random variable vector
        """

        chromosome = list()
        indices = list()
        labels = list()
        for var in self.design_space.basis_set:
            var.get_random()
            chromosome.append(var.value)
            indices.append(var.index)
            labels.append(var.name)
            
        this_ind = self.Individual(items=chromosome, 
                                    names=labels, 
                                    indices=indices, 
                                    fitness_names = self.objective_space.objective_names, 
                                    fitness=self.fitness()
                                    )
        
        #logging.debug("Returned random individual {}".format(this_ind))
        
        return this_ind

    def get_random_population(self,pop_size):
        """Call get_random_mapping n times to generate a list of individuals
        """
        indiv_list = list()
        for idx in range(pop_size):
            indiv_list.append(self.get_random_mapping())

        logging.info("Retrieved {} random mappings from a space of {} elements".format(pop_size, self.design_space.get_cardinality()))

        return indiv_list

    def get_global_search(self):
        tuple_set = list()
        names = list()
        indices = list()
        for variable in self.design_space.basis_set:
            tuple_set.append(variable.variable_tuple)
            names.append(variable.name)
            indices.append(None)

        run_list = list()
        for vector in itertools.product(*tuple_set):
            #print(vector)
            this_indiv = self.individual(names,vector,indices,self.evaluator)
            #print(this_indiv)
            run_list.append(this_indiv)
        #raise
        log_string = "Retrieved {} individuals over {}-dimension design space".format(len(run_list),self.design_space.dimension)
        logging.info(log_string)

        return run_list

    def getHyperCorners(self):
        raise
        pass


def generate_variable_table_class(name):
    """This is a helper function which dynamically creates a new ORM enabled class
    The table will hold the individual values of each variable
    Individual values are stored as a string
    """
    class NewTable( DB_Base ):
        __tablename__ = "vector_{}".format(name)
        #__table_args__ = { 'schema': db }
        id = Column(Integer, primary_key=True)
        value = Column(String)
        def __init__(self,value):
            self.value = str(value)
            
        def __str__(self):
            return self.value
        
        def __repr__(self):
            return self.value    
        
    NewTable.__name__ = name
    return NewTable

class Variable(DB_Base):
    """
    A general variable object, inherited by specific types

    Init Attributes
    name - A label for the variable. Required.
    variable_tuple - The k-Tuple of possible values
    ordered= True - Flag

    Internal Attributes
    index = None - The corresponding index of the generated value
    value = The current value of the variable, defined by the index

    """
    __tablename__ = 'Variables'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)

    def __init__(self,name, variable_tuple, ordered=True, type = "String"):
        self.type = type
        self.name = name
        
        if isinstance(variable_tuple,tuple):
            pass
        elif isinstance(variable_tuple,int):
            variable_tuple = (variable_tuple,)
        elif isinstance(variable_tuple, list):
            variable_tuple = tuple(variable_tuple)
        elif isinstance(variable_tuple, str):
            variable_tuple = tuple([variable_tuple])
        elif isinstance(variable_tuple, float):
            variable_tuple = (variable_tuple,)
        else:
            raise Exception("Need a list, int, float, or tuple")

        try:
            len(variable_tuple)
        except:
            print('Initialize with a list or tuple')
            raise


        # Convert the variable tuple to the database
        # Create the class which holds the

        #print(variable_tuple)

        ValueClass = generate_variable_table_class(name)
        logging.debug("Variable value class; {}".format(ValueClass))
        
        #print(ValueClass)
        #print(dir(ValueClass))
        #print(ValueClass.__init__)
        #this_val = ValueClass(1)
        #print(this_val)
        #print(this_val.value)
        #raise
        #print(this_val)
        #print)

        variable_class_tuple = [ValueClass(val) for val in variable_tuple]
        #print(variable_class_tuple[0])
        #print(variable_class_tuple[0].__table__)
        #print(variable_class_tuple[0])
        #raise
        self.variable_tuple = variable_class_tuple

        self.ordered = ordered

        #self.value_type = type(self.variable_tuple[0])

        self.index = None

        logging.debug("{}".format(self))

    @property
    def value(self):
        return self.variable_tuple[self.index]

    @classmethod
    def from_range(cls, name, lower, resolution, upper):
        """
        Init overload - easy creation from a lower to upper decimal with a step size
        Arguments are string for proper decimal handling!
        """
        # Make sure we have STRING inputs for the decimal case
        if (not (isinstance(lower,str) or isinstance(lower,unicode) )or
            not (isinstance(resolution,str) or isinstance(resolution,unicode) ) or
            not (isinstance(upper,str)or isinstance(upper,unicode) ) ):
            raise TypeError("""Expect all numbers as strings,
            i.e. "0.01" with quotes. This is to ensure decimal precision.\n
            You input: {} - {} - {} Var: {}
            Types: {}, {}, {}
            """.format(lower, resolution, upper, name , type(lower), type(resolution), type(upper)))


        lower = Decimal(lower)
        resolution = Decimal(resolution)
        upper = Decimal(upper)

        assert upper > lower, "Upper range must be > lower"
        assert not (upper - lower) % resolution, "Variable range is not evenly divisble by step size this is not supported.".format(upper,lower, resolution)

        # Assemble a list
        length = (upper - lower) / resolution + 1
        vTuple = [lower + i * resolution for i in range(0,length)]

        return cls(name, vTuple,True)

    @classmethod
    def ordered(cls,name, vTuple):
        """
        Init overload - the variable is ordered (default)
        """
        return cls(name, vTuple,True)

    @classmethod
    def unordered(cls,name, vTuple):
        """
        Init overload - the variable has no ordering
        """
        return cls(name, vTuple,False)

    def get_random(self):
        """
        Return a random value from all possible values
        """

        self.index = random.choice(range(len(self)))


    def get_new_random(self):
        """
        Return a new random value from all possible values
        """
        raise Exception("Obselete??")
        assert(len(self) > 1)

        if self.value == "<UNINITIALIZED>" :
            raise Exception("This variable is not initialized, can't step")
        valueList = list(self.variable_tuple)

        valueList.remove(self.value)
        self.value = random.choice(valueList)

        #self.value
        #return Variable(self.name, self.variable_tuple,self.ordered,self.value)
        return self

    def step_random(self,step_size = 1):
        """ Step in a random direction (up or down) step_size within the possible values
        Must be ordered, otherwise this makes no sense

        """

        assert(self.ordered), "Stepping in variable only makes sense for an ordered list -change to ORDERED"

        if self.value == "<UNINITIALIZED>" :
            raise Exception("This variable is not initialized, can't step without a starting point")

        if self.ordered:
            upperIndexBound = len(self) - 1
            lowerIndexBound = 0
            currentIndex = self.index

            move = random.choice([    1 * step_size   ,   -1 * step_size   ])
            newIndex = currentIndex + move

            if newIndex < lowerIndexBound:
                newIndex = lowerIndexBound
            elif newIndex > upperIndexBound:
                newIndex = upperIndexBound
            else:
                pass

            #print "Upper {} lower {} newIdx {}".format(upperIndexBound, lowerIndexBound, newIndex)
            self.index = newIndex
            #self.value = self.variable_tuple[self.index]

            return self

#        else:
#            return self.get_new_random()

    def val_str(self):
        """
        String for current name and current value
        """
        return "{}[{}] := {}".format(self.name, self.index, self.value)

    def __len__(self):
        """
        The number of possible values
        """
        return len(self.variable_tuple)

    def long_str(self):
        """
        Print all info in variable
        """
        shortTupleString = str(self.variable_tuple)
        maxStrLen = 40
        if len(shortTupleString) > maxStrLen:
            try:
                shortTupleString = "({}, {}, ..., {})".format(str(self.variable_tuple[0]),str(self.variable_tuple[1]),str(self.variable_tuple[-1]))
            except:
                pass

        if self.index == None:
            generatedValueStr = "<UNINITIALIZED>"
        else:
            generatedValueStr = str(self.value)

        if self.ordered:
            ordStr = "Ordered"
        elif not self.ordered:
            ordStr = "Unordered"

        return "{} = {} length: '{}', {}, {}, memory address: {:,d}, {}".format(
                                 self.name,
                                 generatedValueStr,
                                 len(self.variable_tuple),
                                 shortTupleString,
                                 ordStr,
                                 id(self),
                                 self.type,
                                 )


    def __str__(self):
        return self.long_str()

    def next(self):
        """
        Iterator over tuple of values
        Ordering does not matter, will simply return values in the order of the tuple regardless
        """
        if self.iterIndex < len(self.variable_tuple):
            # This is 0 at start
            self.index = self.iterIndex
            #self.value = self.variable_tuple[self.iterIndex]
        else:
            raise StopIteration

        self.iterIndex += 1

        #newValue = self.value

        #return Variable(self.name, self.variable_tuple,self.ordered,self.value)

        return self

    def __iter__(self):
        # Start iteration at 0
        self.iterIndex = 0
        return self


class Objective(DB_Base):
    __tablename__ = 'Objectives'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    goal = Column(String)
    
    def __init__(self, name, goal):
        self.name = name
        self.goal = goal

class ObjectiveSpace(object):
    def __init__(self, objectives):
        objective_names = [obj.name for obj in objectives]
        objective_goals = [obj.goal for obj in objectives]
        
        assert not isinstance(objective_names, basestring)
        assert not isinstance(objective_goals, basestring)
        assert(type(objective_names) == list or type(objective_names) == tuple)
        assert(type(objective_goals) == list or type(objective_names) == tuple)
        assert(len(objective_names) == len(objective_goals))
        for obj in objective_names:
            assert obj not in  ["hash", "start", "finish"]

        for goal in objective_goals:
            assert(goal == "Min" or goal == "Max")

        self.objective_names = objective_names
        self.objective_goals = objective_goals
        logging.debug("Created {}".format(self))

    # Information about the space -------------
    def __str__(self):
        return "ObjectiveSpace: {} Dimensions : {}".format(self.dimension,zip(self.objective_names,self.objective_goals))

    @property
    def dimension(self):
        return len(self.objective_names)


class DesignSpace(object):

    def __init__(self, basis_set):
        """
        The DSpace

        Creation:
        basis_set, a list of Variable objects
        objectives, some text descriptors for the objective space

        Attr:
        dimension: Number of Basis sets
        cardinality: The total number of points
        """


        # Creation
        self.basis_set = basis_set

        #self.objectives = objectives

        self.dimension = self.get_dimension()
        self.cardinality = self.get_cardinality()


        logging.info("Init {0}".format(self))


        for var in self.basis_set:
            assert var.name not in ["hash", "start", "finish"]


    # Representing the space -------------

    def print_design_space(self):
        for var in self.basis_set:
            print(var)

    def __str__(self):
        return "DesignSpace: Dimension: {0}, Cardinality: {1}".format(self.dimension,self.cardinality)


    def get_cardinality(self):
        """
        The cardinality of a set is a measure of the "number of elements of the set"
        """
        size = 1
        for var in self.basis_set:
            size *= len(var)
        return size

    def get_dimension(self):
        """
        The definition of dimension of a space is the number of vectors in a basis
        The dimension of a vector space is the number of vectors in any basis for the space
        """
        return len(self.basis_set)




#class Individual2(list, DB_Base):
class Individual2(list):
    def __init__(self, value_list, names, indices, fitness, fitness_names):
        
        if not names:
            names = [str(i) for i in range(len(value_list))]
        assert len(value_list) == len(names)
        
        self.names = names
        self.fitness = fitness
        self.fitness_names = fitness_names
        super(Individual2, self).__init__(value_list)
        
        # Each item of the list needs it's own attribute defined in class
        for name, index in zip(names,indices):
            setattr(self, name, index)
        
        # Each item of fitness
        for name in self.fitness_names:
            setattr(self, name, None)
        
        
        #print(self.obj1)
        #for name, fit in zip(fitness_names,fitness):
        #    setattr(self, name, fit)            
            #print(name, index)
        #raise
        
        self.hash = self.__hash__()
        self.value_index_str = str(indices)
        
        logging.debug("Individual instantiated; {}".format(self))
    
    def recreate_fitness(self):
        fit_vals = list()
        for name in self.fitness_names:
            fit_vals.append(getattr(self, name))
        #print(self.)
        #print(self.)
        print(self)
        print(self.obj1)
        print(fit_vals)
        raise Exception

                
    def __hash__(self):
        """This defines the uniqueness of the individual
        The ID of an individual could be, for example, the string composed of the variable vectors
        But this would be expensive and complicated to store in a database
        The hash compresses this information to an integer value which should have no collisions
        """
        return hash(tuple(zip(self.names,self[:])))

    def __repr__(self):
        return(self.__str__())
    
    def __str__(self):
        pairs = zip(self.names, self)
        variable_pairs = (["{}={}".format(pair[0],pair[1]) for pair in pairs])
        #fitness_pairs
        this_str = "{} [{}] -> {}: {}".format(self.__hash__(),",".join(variable_pairs), self.fitness.__class__.__name__, self.fitness)

        return(this_str)
    
    def assign_fitness(self):
        #print()
        #print(self.fitness_names)
        #print(self.fitness)
        for name, fit in zip(self.fitness_names,self.fitness.values):
            setattr(self, name, fit)
        #setattr(self, name, fit)        
class Individual(object):
    
    """
    Holds a variable vector with labels;
    chromosome
    labels
    indices


    fitness



    The logic of the variable is stored in the design space basis vectors
    """

    def __init__(self, labels, chromosome, indices, evaluator, fitness = None):
        raise
        self.labels = labels
        self.chromosome = chromosome
        self.indices = indices
        self.evaluator = evaluator
        self.fitness = fitness

    @property
    def evaluated(self):
        if not self.fitness: return False
        else: return True

    def __str__(self):

        name_val_tuple = zip(self.labels, self.chromosome)

        these_pairs = ["{} = {}".format(*this_pair) for this_pair in name_val_tuple]
        thisStr = ", ".join(these_pairs)

        if self.fitness:
            thisStr = thisStr + " -> " + ", ".join(["{}={}".format(fit[0],fit[1]) for fit in self.fitness])
        else:
            thisStr = thisStr + " -> (Unitialized)"
        return thisStr

    # This defines the uniqueness of the individual
    def __eq__(self, other):
        if self.__hash__() == other.__hash__():
            return True
        else:
            return False

    def __hash__(self):
        """This defines the uniqueness of the individual
        The ID of an individual could be, for example, the string composed of the variable vectors
        But this would be expensive and complicated to store in a database
        The hash compresses this information to an integer value which should have no collisions
        """

        return hash(tuple(zip(self.labels,self.chromosome)))

    def __getitem__(self,index):
        return self.chromosome[index]

    def __setitem__(self,index, value):
        raise
        self.chromosome[index],

    def next(self):
        """
        Iterator over tuple of chromosomes
        """
        if self.iterIndex < len(self.chromosome):
            # This is 0 at start
            value = self.chromosome[self.iterIndex]
            self.iterIndex += 1
            return value
        else:
            raise StopIteration

    def __iter__(self):
        # Start iteration at 0
        self.iterIndex = 0
        return self

    def clone(self):
        raise
        clonedIndiv = Individual(self.chromosome)
        return clonedIndiv

    def evaluate(self):
        return self.evaluator(self)