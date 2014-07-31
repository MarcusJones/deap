from __future__ import print_function

from __future__ import division
import random
import warnings

from collections import Sequence
from itertools import repeat
import logging
from decimal import *

#myLogger = logging.getLogger()
#myLogger.setLevel("DEBUG")

######################################
# GA Crossovers                      #
######################################
def mj_list_flip(ind1, ind2, parameters, path_evolog):
    """For the length of chromosome, flip each position between *ind1* and *ind2* with probability *indpb*
    :param ind1: First individual  
    :param ind2: Second individiual
    :param indpb: Probability to flip at position N
    :param path_evolog: Writes the crossover signature to log file
    :returns: ind1,ind2 with modified chromosome and fitness deleted
    """
    indpb = parameters['Probability flip allele']
    
    ind1_original_hash = ind1.hash
    ind2_original_hash = ind2.hash
    new_pairs = list()
    flip_signature = list()
    for pair in zip(ind1.chromosome, ind2.chromosome):
        pair = list(pair)        
        check = random.random()
        flg_flip = '0'
        if check <= indpb:
            pair.reverse()
            flg_flip = 'X'
        flip_signature.append(flg_flip)
        new_pairs.append(pair)
    
    chromo1, chromo2 = zip(*new_pairs)
    ind1.chromosome = chromo1
    ind2.chromosome = chromo2
    ind1.re_init()
    ind2.re_init()
    
    with open(path_evolog, 'a') as evolog:
        print("Crossover; {} x {} [{}] -> {}, {} ".format(ind1_original_hash, ind2_original_hash, "".join(flip_signature), ind1.hash, ind2.hash, ), file=evolog)
    
    del ind1.fitness.values
    del ind2.fitness.values

    
    return(ind1,ind2)


def mj_cxSimulatedBinaryBounded(ind1, ind2, settings, eta):
    
    """-Modifed from DEAP-
    Executes a simulated binary crossover that modify in-place the input
    individuals. The simulated binary crossover expects :term:`sequence`
    individuals of floating point numbers.
    
    :param ind1: The first individual participating in the crossover.
    :param ind2: The second individual participating in the crossover.
    :param eta: Crowding degree of the crossover. A high eta will produce
                children resembling to their parents, while a small eta will
                produce solutions much more different.
    :param low: A value or an :term:`python:sequence` of values that is the lower
                bound of the search space.
    :param up: A value or an :term:`python:sequence` of values that is the upper
               bound of the search space.
    :returns: A tuple of two individuals.

    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.

    .. note::
       This implementation is similar to the one implemented in the 
       original NSGA-II C code presented by Deb.
    """
    size = min(len(ind1), len(ind2))
    if not isinstance(low, Sequence):
        low = repeat(low, size)
    elif len(low) < size:
        raise IndexError("low must be at least the size of the shorter individual: %d < %d" % (len(low), size))
    if not isinstance(up, Sequence):
        up = repeat(up, size)
    elif len(up) < size:
        raise IndexError("up must be at least the size of the shorter individual: %d < %d" % (len(up), size))
    
    for i, xl, xu in zip(xrange(size), low, up):
        if random.random() <= 0.5:
            # This epsilon should probably be changed for 0 since 
            # floating point arithmetic in Python is safer
            if abs(ind1[i] - ind2[i]) > 1e-14: 
                x1 = min(ind1[i], ind2[i])
                x2 = max(ind1[i], ind2[i])
                rand = random.random()
                
                beta = 1.0 + (2.0 * (x1 - xl) / (x2 - x1))
                alpha = 2.0 - beta**-(eta + 1)
                if rand <= 1.0 / alpha:
                    beta_q = (rand * alpha)**(1.0 / (eta + 1))
                else:
                    beta_q = (1.0 / (2.0 - rand * alpha))**(1.0 / (eta + 1))
                
                c1 = 0.5 * (x1 + x2 - beta_q * (x2 - x1))
                
                beta = 1.0 + (2.0 * (xu - x2) / (x2 - x1))
                alpha = 2.0 - beta**-(eta + 1)
                if rand <= 1.0 / alpha:
                    beta_q = (rand * alpha)**(1.0 / (eta + 1))
                else:
                    beta_q = (1.0 / (2.0 - rand * alpha))**(1.0 / (eta + 1))
                c2 = 0.5 * (x1 + x2 + beta_q * (x2 - x1))
                
                c1 = min(max(c1, xl), xu)
                c2 = min(max(c2, xl), xu)
                
                if random.random() <= 0.5:
                    ind1[i] = c2
                    ind2[i] = c1
                else:
                    ind1[i] = c1
                    ind2[i] = c2
    
    return ind1, ind2   




# List of exported function names.
__all__ = []

# Deprecated functions
__all__.extend(['mj_list_flip'])