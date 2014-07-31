from __future__ import print_function
from __future__ import division
#import math
import random

#from itertools import repeat
#from collections import Sequence
#from decimal import *
#import logging
#from copy import deepcopy

######################################
# GA Mutations                       #
######################################
def mj_random_jump(individual, mapping, parameters, path_evolog):
    """Randomly selects a jump between *-jumpsize* and *+jumpsize* for each allele in chromosome
    Jumps that distance in the gene for each allele with probability *indpb*
    Jump is limited to min/max for each gene
    :param individual: individual  
    :param mapping: Used to access the genes and the indices of the genes
    :param jumpsize: = parameters['Jump size'] Probability to flip at position N
    :param indpb: = parameters['Probability mutation'] Probability to jump at position N
    :param path_evolog: Writes the mutation signature to log file
    :returns: individual: Individual with mutated chromosome and deleted fitness
    """        
    jumpsize = parameters['Jump size']
    indpb =   parameters['Probability mutation']      
    
    jump_digits = len(str(jumpsize)) + 1
    
    for allele in individual.chromosome:
        assert allele.vtype == 'float'
        assert allele.ordered    
        
    original = individual.clone()
    mutated_ind =     individual.clone()

    original_hash = original.hash
    possible_jumps = range(-jumpsize,jumpsize+1,1)
    possible_jumps.remove(0)
    
    mutate_signature = list()

    new_chromo = list()

    assert(len(mapping.design_space.basis_set) == len(mutated_ind.chromosome)), "{}".format(mutated_ind)
    
    for allele in mutated_ind.chromosome:

        gene = mapping.design_space.basis_set[allele.locus]
        assert(allele.name == gene.name)
        gene.index = allele.index

        index_max = len(gene.variable_tuple)-1
        index_min = 0
        
        check = random.random()
        jump = ""
        if check <= indpb:
            jump = random.choice(possible_jumps)
            newindex = gene.index + jump
            if newindex < index_min:
                newindex = index_min
            if newindex > index_max:
                newindex = index_max
            gene.index = newindex
        mutate_signature.append(jump)
        new_chromo.append(gene.return_allele())
        #raise
    
    mutated_ind.chromosome = new_chromo
    mutated_ind.re_init()
    mutate_signature = ['{number:{width}}'.format(width=jump_digits, number=jsize) for jsize in mutate_signature]
    
    with open(path_evolog, 'a') as evolog:
        print("{:15} [{}] {}".format(original_hash, "|".join(mutate_signature), mutated_ind.hash),file=evolog, )

    del mutated_ind.fitness.values
    
    return mutated_ind

def mut_poly_calc(ind_original_val, xl, xu, eta):
    x = ind_original_val
    delta_1 = (x - xl) / (xu - xl)
    delta_2 = (xu - x) / (xu - xl)
    rand = random.random()
    mut_pow = 1.0 / (eta + 1.)

    if rand < 0.5:
        xy = 1.0 - delta_1
        val = 2.0 * rand + (1.0 - 2.0 * rand) * xy**(eta + 1)
        delta_q = val**mut_pow - 1.0
    else:
        xy = 1.0 - delta_2
        val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * xy**(eta + 1)
        delta_q = 1.0 - val**mut_pow

    x = x + delta_q * (xu - xl)
    x = min(max(x, xl), xu)
    ind_new_val = x
    return ind_new_val

def mj_mutPolynomialBounded(individual, mapping, parameters, path_evolog):
    """Polynomial mutation as implemented in original NSGA-II algorithm in
    C by Deb.
    
    :param individual: :term:`Sequence <sequence>` individual to be mutated.
    :param eta: Crowding degree of the mutation. A high eta will produce
                a mutant resembling its parent, while a small eta will
                produce a solution much more different.
    :param low: A value or a :term:`python:sequence` of values that
                is the lower bound of the search space.
    :param up: A value or a :term:`python:sequence` of values that
               is the upper bound of the search space.
    :returns: A tuple of one individual.
    """
    
    eta = parameters['Crowding degree']
    indpb = parameters['indpb']
    
    size = len(individual)
    low = list()
    up = list()
    original_hash = individual.hash
    for allele, gene in zip(individual.chromosome, mapping.design_space.basis_set):
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
    
    #===========================================================================
    # Loop over chromosome
    #===========================================================================
    jump = ""
    new_chromosome = list()
    mutate_signature = list()
    for i, xl, xu in zip(xrange(size), low, up):
        this_gene = mapping.design_space.basis_set[i]
        this_allele = individual.chromosome[i]
        this_allele_val = float(this_allele.value)
        old_index = this_allele.index
        assert(this_gene.locus == this_allele.locus)
        
        if random.random() <= indpb:
            new_val = mut_poly_calc(this_allele_val, xl, xu, eta)
            new_allele = this_gene.return_closest_allele(new_val)
            new_index = new_allele.index
            jump = str(old_index-new_index)
        else:
            new_allele = this_allele
            jump = ""
        new_chromosome.append(new_allele)
        mutate_signature.append(jump)
    
    #===========================================================================
    # Reassign individual
    #===========================================================================
    individual.chromosome = new_chromosome

    del individual.fitness.values

    #===========================================================================
    # Print to log
    #===========================================================================
    
    jump_digits = len(str(max(mutate_signature))) + 1
    jump_digits = 3
    #print(mutate_signature)
    #print(jump_digits)
    mutate_signature = ['{number:{width}}'.format(width=jump_digits, number=jsize) for jsize in mutate_signature]
    with open(path_evolog, 'a') as evolog:
        print("{:15} [{}] {}".format(original_hash, "|".join(mutate_signature), individual.hash),file=evolog, )
    
    return individual



__all__ = ['mj_random_jump', 'mj_mutPolynomialBounded']
