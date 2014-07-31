from __future__ import print_function
from __future__ import division
import math
import random

from itertools import repeat
from collections import Sequence
from decimal import *
import logging
from copy import deepcopy

######################################
# GA Mutations                       #
######################################
def mj_random_jump(individual, mapping, jumpsize, indpb, path_evolog):
        

    jump_digits = len(str(123))
    
    for allele in individual.chromosome:
        assert allele.vtype == 'float'
        assert allele.ordered    
        
    original = individual.clone()
    mutated_ind =     individual.clone()
    
    #print(mutated_ind)
    #raise
    
    original_hash = original.hash
    possible_jumps = range(-jumpsize,jumpsize+1,1)
    possible_jumps.remove(0)
    
    mutate_signature = list()
    #print("Before",individual.chromosome)   
    #print("Before", individual.hash)
    new_chromo = list()

    for allele in mutated_ind.chromosome:
        
        #print()
        #print(allele.locus)
        #print(allele)
        
        gene = mapping.design_space.basis_set[allele.locus]
        assert(allele.name == gene.name)
        gene.index = allele.index
        
        #print(gene)
        #raise
        
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

__all__ = ['mj_random_jump']
