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
def mj_list_flip(ind1, ind2, mapping, parameters, path_evolog):
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

def cx_sim_binary_calc(ind1_val, ind2_val, xl, xu,eta):
    
    x1 = min(ind1_val, ind2_val)
    x2 = max(ind1_val, ind2_val)
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
        ind1_new_val = c2
        ind2_new_val = c1
    else:
        ind1_new_val = c1
        ind2_new_val = c2

    return ind1_new_val,ind2_new_val

def mj_cxSimulatedBinaryBounded(ind1, ind2, mapping, parameters, path_evolog):
    
    """-Modifed from DEAP-
    Executes a simulated binary crossover that modify in-place the input
    individuals. The simulated binary crossover expects :term:`sequence`
    individuals of floating point numbers.
    
    :param ind1: The first individual participating in the crossover.
    :param ind2: The second individual participating in the crossover.
    :param eta: =parameters['Crowding degree']; Crowding degree of the crossover. A high eta will produce
                children resembling to their parents, while a small eta will
                produce solutions much more different.
    :param low: =mapping; A value or an :term:`python:sequence` of values that is the lower
                bound of the search space.
    :param up: =mapping; A value or an :term:`python:sequence` of values that is the upper
               bound of the search space.
    :returns: A tuple of two individuals.

    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.

    .. note::
       This implementation is similar to the one implemented in the 
       original NSGA-II C code presented by Deb.
    """
    eta = parameters['Crowding degree']
    
    ind1_original_hash = ind1.hash
    ind2_original_hash = ind2.hash
    
    size = len(ind1.chromosome)
    low = list()
    up = list()
    for allele, gene in zip(ind1.chromosome, mapping.design_space.basis_set):
        assert(gene.vtype == 'float')
        assert(allele.name == gene.name )
        assert(allele.locus ==gene.locus)
        assert(allele.vtype == gene.vtype)     
        low_val = gene.variable_tuple[0].value
        low_val = float(low_val)
        low.append(low_val)
        up_val = gene.variable_tuple[-1].value
        up_val = float(up_val)
        up.append(up_val)
        
    ind1_new_chromo = list()
    ind2_new_chromo = list()
    cx_signature = list()
    for i, xl, xu in zip(xrange(size), low, up):
        flg_cx = '0'
        this_gene = mapping.design_space.basis_set[i]
        
        ind1_allele = ind1.chromosome[i]
        ind1_val = float(ind1_allele.value)
        
        ind2_allele = ind2.chromosome[i]
        ind2_val = float(ind2_allele.value)
        assert(this_gene.locus == ind1_allele.locus == ind2_allele.locus)
                
        # Flip this allele only if probability threshold passed
        if random.random() <= parameters['Probability crossover allele']: # 0.5 in original 
            flg_cx = 'X'

            
            # If they are exact, do not flip
            if ind1_val != ind2_val:
                # Do the sim binary cx calculation here
                ind1_new_val, ind2_new_val = cx_sim_binary_calc(ind1_val, ind2_val, xl, xu,eta)
                    
                ind1_new_chromo.append(this_gene.return_closest_allele(ind1_new_val))
                ind2_new_chromo.append(this_gene.return_closest_allele(ind2_new_val))
            else: 
                ind1_new_chromo.append(ind1_allele)
                ind2_new_chromo.append(ind2_allele)
                            
        # Just append the original allele to the chromosome if there is no flip on this allele
        else:
            ind1_new_chromo.append(ind1_allele)
            ind2_new_chromo.append(ind2_allele)
        
        cx_signature.append(flg_cx)
    
    ind1.chromosome = ind1_new_chromo
    ind2.chromosome = ind2_new_chromo
 
    
    del ind1.fitness.values
    del ind2.fitness.values

    with open(path_evolog, 'a') as evolog:
        print("Crossover; {:>15} x {:<15} [{}] -> {:>15}, {:<15}".format(ind1_original_hash, ind2_original_hash, "".join(cx_signature), ind1.hash, ind2.hash, ), file=evolog)

    assert(len(mapping.design_space.basis_set) == len(ind1.chromosome)), "{}".format(ind1)
    assert(len(mapping.design_space.basis_set) == len(ind2.chromosome)), "{}".format(ind2)

    return ind1, ind2   




# List of exported function names.
__all__ = []

# Deprecated functions
__all__.extend(['mj_list_flip', 'mj_cxSimulatedBinaryBounded'])