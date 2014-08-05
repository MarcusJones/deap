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
from mj_config.deapconfig import *
import logging.config

# Standard library
from decimal import Decimal
import random
import time
import itertools
import sys
import imp
import datetime

# External library
import numpy as np


# Utilites
import sqlalchemy as sa
import utility_SQL_alchemy as util_sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table
from copy import deepcopy

from mj_utilities.db_base import DB_Base

from operator import mul, truediv

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

#--- Database interaction
def convert_DB_individual(res, mapping):
    """Given a Results object from the database, recreate the Individual object
    """
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
    
    this_res.start = ind.start_time
    this_res.finish = ind.finish_time
    
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
        attr_dict["var_c_{}".format(var.name)] = sa.Column("var_c_{}".format(var.name), sa.Integer, sa.ForeignKey('vector_{}.id'.format(var.name)), nullable = False,  ) 
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

#--- Objective space
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

class Fitness(object):
    """The fitness is a measure of quality of a solution. If *values* are
    provided as a tuple, the fitness is initalized using those values,
    otherwise it is empty (or invalid).
    
    :param values: The initial values of the fitness as a tuple, optional.

    Fitnesses may be compared using the ``>``, ``<``, ``>=``, ``<=``, ``==``,
    ``!=``. The comparison of those operators is made lexicographically.
    Maximization and minimization are taken care off by a multiplication
    between the :attr:`weights` and the fitness :attr:`values`. The comparison
    can be made between fitnesses of different size, if the fitnesses are
    equal until the extra elements, the longer fitness will be superior to the
    shorter.

    Different types of fitnesses are created in the :ref:`creating-types`
    tutorial.

    .. note::
       When comparing fitness values that are **minimized**, ``a > b`` will
       return :data:`True` if *a* is **smaller** than *b*.
    """
    
    weights = None
    """The weights are used in the fitness comparison. They are shared among
    all fitnesses of the same type. When subclassing :class:`fitness`, the
    weights must be defined as a tuple where each element is associated to an
    objective. A negative weight element corresponds to the minimization of
    the associated objective and positive weight to the maximization.

    .. note::
        If weights is not defined during subclassing, the following error will 
        occur at instantiation of a subclass fitness object: 
        
        ``TypeError: Can't instantiate abstract <class fitness[...]> with
        abstract attribute weights.``
    """
    
    wvalues = ()
    """Contains the weighted values of the fitness, the multiplication with the
    weights is made when the values are set via the property :attr:`values`.
    Multiplication is made on setting of the values for efficiency.
    
    Generally it is unnecessary to manipulate wvalues as it is an internal
    attribute of the fitness used in the comparison operators.
    """
    
    def __init__(self, values=()):
        if self.weights is None:
            raise TypeError("Can't instantiate abstract %r with abstract "
                "attribute weights." % (self.__class__))
        
        if not isinstance(self.weights, Sequence):
            raise TypeError("Attribute weights of %r must be a sequence." 
                % self.__class__)
        
        if len(values) > 0:
            self.values = values
        
        #logging.debug("New fitness {}".format(self))
        
    def getValues(self):
        try:
            result = tuple(map(truediv, self.wvalues, self.weights))
        except:
            print("wvalues: {} weights: {}".format(self.wvalues, self.weights))
            raise
        return result
    
    def setValues(self, values):
        try:
            self.wvalues = tuple(map(mul, values, self.weights))
        except TypeError:
            _, _, traceback = sys.exc_info()
            raise TypeError, ("Both weights and assigned values must be a "
            "sequence of numbers when assigning to values of "
            "%r. Currently assigning value(s) %r of %r to a fitness with "
            "weights %s."
            % (self.__class__, values, type(values), self.weights)), traceback
            
    def delValues(self):
        self.wvalues = ()

    values = property(getValues, setValues, delValues,
        ("fitness values. Use directly ``individual.fitness.values = values`` "
         "in order to set the fitness and ``del individual.fitness.values`` "
         "in order to clear (invalidate) the fitness. The (unweighted) fitness "
         "can be directly accessed via ``individual.fitness.values``."))
    
    def dominates(self, other, obj=slice(None)):
        """Return true if each objective of *self* is not strictly worse than 
        the corresponding objective of *other* and at least one objective is 
        strictly better.

        :param obj: Slice indicating on which objectives the domination is 
                    tested. The default value is `slice(None)`, representing
                    every objectives.
        """
        not_equal = False
        for self_wvalue, other_wvalue in zip(self.wvalues[obj], other.wvalues[obj]):
            if self_wvalue > other_wvalue:
                not_equal = True
            elif self_wvalue < other_wvalue:
                return False                
        return not_equal

    @property
    def valid(self):
        """Assess if a fitness is valid or not."""
        return len(self.wvalues) != 0
        
    def __hash__(self):
        return hash(self.wvalues)

    def __gt__(self, other):
        return not self.__le__(other)
        
    def __ge__(self, other):
        return not self.__lt__(other)

    def __le__(self, other):
        return self.wvalues <= other.wvalues

    def __lt__(self, other):
        return self.wvalues < other.wvalues

    def __eq__(self, other):
        return self.wvalues == other.wvalues
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __deepcopy__(self, memo):
        """Replace the basic deepcopy function with a faster one.
        
        It assumes that the elements in the :attr:`values` tuple are 
        immutable and the fitness does not contain any other object 
        than :attr:`values` and :attr:`weights`.
        """
        copy_ = self.__class__()
        copy_.wvalues = self.wvalues
        return copy_

    def __str__(self):
        """Return the values of the fitness object."""
        return str(self.values if self.valid else "EMPTY FITNESS")

    def __repr__(self):
        """Return the Python code to build a copy of the object."""
        return "%s.%s(%r)" % (self.__module__, self.__class__.__name__,
            self.values if self.valid else tuple())


#--- Design space

class Allele(object):
    """
    Init Attributes
    name - A label for the variable. Required.
    locus - 
    variable_tuple - The k-Tuple of possible values
    ordered= True - Flag

    Internal Attributes
    index = None - The corresponding index of the generated value
    value = The current value of the variable, defined by the index
    """
    def __init__(self, name, locus, vtype, value, index, ordered):
        self.name = name
        self.locus = locus
        self.vtype = vtype
        self.value = value
        self.index = index
        self.ordered = ordered

        #logging.debug("{}".format(self))
    
    def __str__(self):
        return self.this_val_str()

    def __repr__(self):
        return self.this_val_str()
    
    @property
    def val_str(self):
        return str(self.value)
    
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

    def __init__(self, name, vtype, variable_tuple, ordered):
        self.vtype = vtype
        self.name = name
        self.locus = -1
        
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

        self.ValueClass = generate_variable_table_class(name)
        #logging.debug("Variable value class; {}".format(self.ValueClass))

        variable_class_tuple = [self.ValueClass(val) for val in variable_tuple]

        self.variable_tuple = variable_class_tuple

        self.ordered = ordered

        self.index = None

        logging.debug("{}".format(self))

    @property
    def value_ORM(self):
        return self.variable_tuple[self.index]
    
    @property
    def val_str(self):
        return str(self.variable_tuple[self.index])

    @property
    def value(self):
        return self.variable_tuple[self.index]

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

        return cls(name, vtype, vTuple, True)

    @classmethod
    def ordered(cls, name, vtype, vTuple):
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
        #raise
        self.index = index
        return Allele(self.name, 
                      self.locus,                      
                              self.vtype, 
                              self.val_str, 
                              self.index, 
                              self.ordered)

    def return_allele(self):
        return Allele(self.name, 
                      self.locus,
                              self.vtype, 
                              self.val_str, 
                              self.index, 
                              self.ordered)

    def return_closest_allele(self,target_value):
        
        assert self.vtype == 'float'

        # Get values as list of floats for comparison
        possible_values = [float(val.value) for val in  self.variable_tuple]
        # Get closest
        closest = min(possible_values, key=lambda x:abs(x-target_value))
        
        # Get the index of this value and update variable index to match
        closest_index= possible_values.index(closest)
        self.index = closest_index
        
        return Allele(self.name, 
              self.locus,
                      self.vtype, 
                      self.val_str, 
                      self.index, 
                      self.ordered)

         
    def return_random_allele(self):
        """
        Return a random value from all possible values
        """

        self.index = random.choice(range(len(self)))
        
        return Allele(self.name, 
                      self.locus,
                              self.vtype, 
                              self.val_str, 
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

        return self

    def step_random(self, start_index, step_size = 1):
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

            self.index = newIndex

            return self

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
            generatedValueStr = self.val_str

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
    
    def __repr__(self):
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
        for i,var in enumerate(basis_set):
            var.locus = i
        
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
    """An individual is composed of a list of alleles (chromosome)
    Each gene is an instance of the Variable class
    The Individual class inherits list (slicing, assignment, mutability, etc.)
    """
    def __init__(self, chromosome, fitness):
        
        for val in chromosome:
            assert type(val) == Allele

        
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
        
        
        self.start_time = None
        self.finish_time = None
        #self.hash = self.__hash__()
        
        #logging.debug("Individual instantiated; {}".format(self))
        
    @property    
    def hash(self):
        return self.__hash__()
    
    
    def clone(self):
        new_chromo = list()
        for allele in self.chromosome:
            new_chromo.append(Allele(allele.name, allele.locus, allele.vtype, allele.value, allele.index, allele.ordered))
                              
        cloned_Ind = Individual2(new_chromo, deepcopy(self.fitness))
        assert(cloned_Ind is not self)
        assert(cloned_Ind.fitness is not self.fitness)
        return cloned_Ind

    
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
        
        index_list = [allele.index for allele in self.chromosome]
        return hash(tuple(index_list))
        #return hash(tuple(zip(self[:])))

    def __eq__(self,other):
        if self.hash == other.hash:
            return True
        return False

    #def __repr__(self):
    #    return(self.__str__())
    
    def __str__(self):
        return "{:>12}; {}, fitness:{}".format(self.hash, ", ".join([var.this_val_str() for var in self.chromosome]), self.fitness)

    def update(self):
        """Check on the status of the process, update if necessary
        """
        if self.process:
            retcode = self.process.poll()
            # Windows exit code
            if retcode is None:
                #logging.debug("Update {}, Process: {}, RUNNING".format(self.hash,self.process))                
                self.status = "Running"
            else:
                # Add more handling for irregular retcodes
                # See i.e. http://www.symantec.com/connect/articles/windows-system-error-codes-exit-codes-description
                #logging.debug("Update {}, Process: {}, DONE".format(self.hash,self.process))                
                self.run_status = "Finished"
                self.finish_time  = datetime.datetime.now()
        else:
            # This process has not been started]
            raise
            pass


#--- Evolution


class Mapping(object):
    def __init__(self, design_space, objective_space):
        self.design_space = design_space
        self.objective_space = objective_space
        logging.info(self)

    def __str__(self):
        return "Mapping dimension {} domain to dimension {} range".format(self.design_space.dimension,
                                                                  self.objective_space.dimension)
    #---Assignment
    def assign_individual(self, Individual):
        self.Individual = Individual
        logging.info("This mapping will produce individuals of class {}".format(Individual.__name__))

    def assign_evaluator(self, life_cycle):
        self.Individual.pre_process  = life_cycle['pre_process']
        self.Individual.execute  = life_cycle['execute']
        self.Individual.post_process  = life_cycle['post_process']
        
        logging.info("Bound life cycle {}, {}, {} to {}".format(
                                                                life_cycle['pre_process'],
                                                                life_cycle['execute'],
                                                                life_cycle['post_process'],
                                                                self.Individual.__name__)
                     )

    def assign_fitness(self, Fitness):
        self.fitness = Fitness
        logging.info("This mapping will produce fitness of class {}".format(Fitness.__name__))
    
    #--- Generating points in the space
    def get_random_mapping(self, flg_verbose = False):
        """
        Randomly sample all basis_set vectors, return a random variable vector
        """
        chromosome = list()
        for var in self.design_space.basis_set:
            this_var = var.return_random_allele()
            chromosome.append(this_var)

        this_ind = self.Individual(chromosome=chromosome, 
                                    fitness=self.fitness()
                                    )
        #this_ind = this_ind.init_life_cycle()
        
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
        raise
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

class Generation(DB_Base):
    __tablename__ = 'Generations'
    id = Column(Integer, primary_key=True)
    gen = Column(Integer, nullable = False)    
    individual = Column(Integer, sa.ForeignKey('Results.hash'), nullable = False,)
    
    
    def __init__(self, gen, individual):
        self.gen = gen
        self.individual = individual


