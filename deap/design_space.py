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
from copy import deepcopy

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

#--- Database
def convert_DB_individual(res, mapping):
    chromosome = list()
    for var in mapping.design_space.basis_set:
        index_from_db = getattr(res, "var_c_{}".format(var.name))
        index = index_from_db - 1
        this_var = var.get_indexed_obj(index)
        chromosome.append(this_var)

    fitvals = list()
    for name in mapping.objective_space.objective_names:
        val = getattr(res, "obj_c_{}".format(name))
        fitvals.append(val)

    this_fit = mapping.fitness()
    this_fit.setValues(fitvals)

    this_ind = mapping.Individual(chromosome=chromosome, 
                                fitness=this_fit
                                )

    return this_ind

def convert_individual_DB(ResultsClass,ind):
    this_res = ResultsClass()
    this_res.hash = ind.hash
    
    for gene in ind.chromosome:
        setattr(this_res, "var_c_{}".format(gene.name),gene.index+1)

    for name,val in zip(ind.fitness.names,ind.fitness.values):
        setattr(this_res, "obj_c_{}".format(name),val)

    return this_res



def generate_individuals_table(mapping):
    columns = list()
    columns.append(sa.Column('hash', sa.Integer, primary_key=True))
    columns.append(sa.Column('start', sa.DateTime))
    columns.append(sa.Column('finish', sa.DateTime))    
    for var in mapping.design_space.basis_set:
        columns.append(sa.Column("var_c_{}".format(var.name), sa.Integer, sa.ForeignKey('vector_{}.id'.format(var.name)), nullable = False,  ))
    for obj in mapping.objective_space.objective_names:
        #columns.append(sa.Column("{}".format(obj), sa.Float, nullable = False,  ))
        columns.append(sa.Column("obj_c_{}".format(obj), sa.Float))
    
    tab_results = sa.Table('Results', DB_Base.metadata, *columns)
    
    return(tab_results)  

def generate_ORM_individual(mapping):
    def __str__(self):
        return "XXX"
        #return ", ".join(var in mapping.design_space.basis_set)
    def __repr__(self):
        #return ",".join(dir(self))
        return "{} {} {}".format(self.hash, self.start, self.finish)
        #return ", ".join(var in mapping.design_space.basis_set)  
    attr_dict = {
                    '__tablename__' : 'Results',
                    'hash' : sa.Column(Integer, primary_key=True),
                    'start' : sa.Column('start', sa.DateTime),
                    'finish' : sa.Column('finish', sa.DateTime),
                    '__str__' : __str__,
                    '__repr__' : __repr__,
                }
    for var in mapping.design_space.basis_set:
        attr_dict["var_c_{}".format(var.name)] =sa.Column("var_c_{}".format(var.name), sa.Integer, sa.ForeignKey('vector_{}.id'.format(var.name)), nullable = False,  ) 
    for obj in mapping.objective_space.objective_names:
        attr_dict["obj_c_{}".format(obj)] =  sa.Column("obj_c_{}".format(obj), sa.Float)
    
    ThisClass = type('Results',(object,),attr_dict)


    return ThisClass

def generate_variable_table_class(name):
    """This is a helper function which dynamically creates a new ORM enabled class
    The table will hold the individual values of each variable
    Individual values are stored as a string
    """

    class NewTable( DB_Base ):
        __tablename__ = "vector_{}".format(name)
        #__table_args__ = { 'schema': db }
        id = Column(Integer, primary_key=True)
        value = Column(String(16), nullable=False, unique=True)
        def __init__(self,value):
            self.value = str(value)
            
        def __str__(self):
            return self.value
        
        def __repr__(self):
            return self.value    
        
       
    NewTable.__name__ = "vector_ORM_{}".format(name)

    
    return NewTable



#---

def evaluate_population(population, engine):
    raise
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

    def assign_fitness(self, Fitness):
        self.fitness = Fitness
        logging.info("This mapping will produce fitness of class {}".format(Fitness.__name__))
    
    def clone_ind(self, ind):
        return Individual2(ind.chromosome, self.fitness())
    
    # Generating points in the space-------------
    def get_random_mapping(self, flg_verbose = False):
        """
        Randomly sample all basis_set vectors, return a random variable vector
        """
        
        chromosome = list()
        #indices = list()
        #vtypes = list()
        #labels = list()
        for var in self.design_space.basis_set:
            this_var = var.get_random_obj()
            chromosome.append(this_var)
            #indices.append(var.index)
            #vtypes.append(var.vtype)
            #labels.append(var.name)

        #logging.debug("Chromosome [0]:{} {}".format(type(chromosome[0]),chromosome[0]))
        
        
        this_ind = self.Individual(chromosome=chromosome, 
                                    #names=labels,
                                    #vtypes = vtypes,
                                    #indices=indices, 
                                    #fitness_names = self.objective_space.objective_names, 
                                    fitness=self.fitness()
                                    )
        if flg_verbose:
            logging.debug("Creating a {} individual with chromosome {}".format(self.Individual, chromosome))        
            logging.debug("Returned random individual {}".format(this_ind))
        
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


class VariableObject(object):
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
    def __init__(self, name, vtype, variable_tuple, index, ordered):
        self.name = name
        self.vtype = vtype
        self.variable_tuple = variable_tuple
        self.index = index
        self.ordered = ordered

        #logging.debug("{}".format(self))
    
    def __str__(self):
        return self.this_val_str()
    
    @property
    def val_str(self):
        return str(self.variable_tuple[self.index])
    
    def this_val_str(self):
        
        """
        String for current name and current value
        """
        return "{}[{}]={}".format(self.name, self.index, self.val_str)


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
    vtype = Column(String)

    def __init__(self,name, vtype, variable_tuple, ordered):
        self.vtype = vtype
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

        self.ValueClass = generate_variable_table_class(name)
        logging.debug("Variable value class; {}".format(self.ValueClass))
        
        #print(ValueClass)
        #print(dir(ValueClass))
        #print(ValueClass.__init__)
        #this_val = ValueClass(1)
        #print(this_val)
        #print(this_val.value)
        #raise
        #print(this_val)
        #print)

        variable_class_tuple = [self.ValueClass(val) for val in variable_tuple]
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
    def value_ORM(self):
        return self.variable_tuple[self.index]
    
    @property
    def val_str(self):
        return str(self.variable_tuple[self.index])
    
    @classmethod
    def from_range(cls, name, vtype, lower, resolution, upper):
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

        return cls(name, vtype, vTuple,True)

    @classmethod
    def ordered(cls,name, vtype, vTuple):
        """
        Init overload - the variable is ordered (default)
        """
        return cls(name, vtype, vTuple,True)

    @classmethod
    def unordered(cls,name, vtype, vTuple):
        """
        Init overload - the variable has no ordering
        """
        return cls(name, vtype, vTuple,False)

    def get_random(self):
        """
        Return a random value from all possible values
        """

        self.index = random.choice(range(len(self)))
        return self

    def get_indexed_obj(self, index):
        self.index = index
        return VariableObject(self.name, 
                              self.vtype, 
                              self.variable_tuple, 
                              self.index, 
                              self.ordered)
        
    def get_random_obj(self):
        """
        Return a random value from all possible values
        """

        self.index = random.choice(range(len(self)))
        
        
        return VariableObject(self.name, 
                              self.vtype, 
                              self.variable_tuple, 
                              self.index, 
                              self.ordered)


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

    def this_val_str(self):
        
        """
        String for current name and current value
        """
        return "{}[{}] := {}".format(self.name, self.index, self.val_str)

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
                                 self.vtype,
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


class Generation(DB_Base):
    __tablename__ = 'Generations'
    id = Column(Integer, primary_key=True)
    gen = Column(Integer, nullable = False)    
    individual = Column(Integer, sa.ForeignKey('Results.hash'), nullable = False,)
    
    
    def __init__(self, gen, individual):
        self.gen = gen
        self.individual = individual



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

        #for goal in objective_goals:
        #    assert(goal == "Min" or goal == "Max")

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



class Individual2(list):
    """An individual is composed of a list of genes (chromosome)
    Each gene is an instance of the Variable class
    The Individual class inherits list (slicing, assignment, mutability, etc.)
    """
    def __init__(self, chromosome, fitness):
        
        for val in chromosome:
            assert type(val) == VariableObject

        list_items = list()
        for gene in chromosome:
            if gene.vtype == 'float':
                list_items.append(float(gene.val_str))
            elif gene.vtype == 'string':
                list_items.append(gene.val_str)
            else:
                raise Exception("{}".format(gene.vtype))
        super(Individual2, self).__init__(list_items)
        
        self.chromosome = chromosome
        self.fitness = fitness
        #self.hash = self.__hash__()
        
        #logging.debug("Individual instantiated; {}".format(self))
        
    @property    
    def hash(self):
        return self.__hash__()
    
    def re_init(self):
        list_items = list()
        for gene in self.chromosome:
            if gene.vtype == 'float':
                list_items.append(float(gene.val_str))
            elif gene.vtype == 'string':
                list_items.append(gene.val_str)
            else:
                raise Exception("{}".format(gene.vtype))      
        super(Individual2, self).__init__(list_items)
        
    
    def recreate_fitness(self):
        raise
        fit_vals = list()
        for name in self.fitness_names:
            fit_vals.append(getattr(self, name))
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
        
        index_list = [gene.index for gene in self.chromosome]
        return hash(tuple(index_list))
        #return hash(tuple(zip(self[:])))

    #def __repr__(self):
    #    return(self.__str__())
    
    def __str__(self):
        return "{:>12}; {}, fitness:{}".format(self.hash, ", ".join([var.this_val_str() for var in self.chromosome]), self.fitness)
                              #str() + ) #+ ", ".join([str(id(gene)) for gene in self.chromosome])
        
#         name_idx_val = zip(self.names, self.indices, self)
# 
#         variable_str = ", ".join(["{}[{}]={}".format(*triplet) for triplet in name_idx_val])
# 
#         fitness_str = "{}={}".format(self.fitness_names,self.fitness)
#         
#         #fitness_str = ", ".join(["{}={}".format(*triplet) for triplet in zip(self.fitness_names,self.fitness)])
#         
#         this_str = "{} {} ({}) -> {}".format(self.__hash__(),variable_str,",".join(self.vtypes),fitness_str)
#         return(this_str)
    
    def assign_fitness(self):
        raise
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