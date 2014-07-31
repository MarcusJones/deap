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
def mj_list_flip(ind1, ind2, indpb, path_evolog):
    """For the length of chromosome, flip each position between *ind1* and *ind2* with probability *indpb*
    :param ind1: First individual  
    :param ind2: Second individiual
    :param indpb: Probability to flip at position N
    :param path_evolog: Writes the crossover signature to log file
    :returns: ind1,ind2 with modified chromosome and fitness deleted
    """
    
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






# List of exported function names.
__all__ = []

# Deprecated functions
__all__.extend(['mj_list_flip'])