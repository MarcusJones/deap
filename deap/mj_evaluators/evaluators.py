
import random
from math import sin, cos, pi, exp, e, sqrt
from operator import mul
from functools import reduce
from decimal import Decimal
import logging

def mj_zdt1_decimal(settings,individual):
    """ZDT1 multiobjective function.
    
    :math:`g(\\mathbf{x}) = 1 + \\frac{9}{n-1}\\sum_{i=2}^n x_i`
    
    :math:`f_{\\text{ZDT1}1}(\\mathbf{x}) = x_1`
    
    :math:`f_{\\text{ZDT1}2}(\\mathbf{x}) = g(\\mathbf{x})\\left[1 - \\sqrt{\\frac{x_1}{g(\\mathbf{x})}}\\right]`
    """
    values = list(individual[:])
    #print(values)
    #raise
    #val = values[0]
    #print(val)
    #print(type(val))
    #print(type(val.value))
    
    #raise
    #print(values)
    try:
        values = [float(val.value) for val in values]
    except AttributeError:
        pass
    #values = [float(str(val.value)) for val in values]
    #print(values)
    #print(type(values[0]))
    #print(type(values[0].value))
    #print(float(values[0].value))
    #raise
    #individual[:] = values
    #print(individual)
    #raise
    g  = 1.0 + 9.0*sum(values[1:])/(len(values)-1)
    f1 = values[0]
    f2 = g * (1 - sqrt(f1/g))
    
    #this_fit = individual.fitness
    individual.fitness.setValues((f1, f2))
    #print(this_fit)
    #individual.fitness = this_fit
    #raise Exception
    #individual.fitness.values = (f1, f2)
    
    logging.debug("Evaluated {} -> {}".format(values, individual.fitness))
    
    return individual




def mj_zdt1_decimal_exe(settings,individual):
    raise
    """ZDT1 multiobjective function.
    
    :math:`g(\\mathbf{x}) = 1 + \\frac{9}{n-1}\\sum_{i=2}^n x_i`
    
    :math:`f_{\\text{ZDT1}1}(\\mathbf{x}) = x_1`
    
    :math:`f_{\\text{ZDT1}2}(\\mathbf{x}) = g(\\mathbf{x})\\left[1 - \\sqrt{\\frac{x_1}{g(\\mathbf{x})}}\\right]`
    """
    values = list(individual[:])
    try:
        values = [float(val.value) for val in values]
    except AttributeError:
        pass

    g  = 1.0 + 9.0*sum(values[1:])/(len(values)-1)
    f1 = values[0]
    f2 = g * (1 - sqrt(f1/g))
    
    individual.fitness.setValues((f1, f2))

    
    logging.debug("Evaluated {} -> {}".format(values, individual.fitness))
    
    return individual