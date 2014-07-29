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
    #for gene in ind1.chromosome:
    #    assert gene.vtype == 'float'
    #    assert gene.ordered    
    
    #print([gene.index for gene in ind1.chromosome])
    #print([gene.index for gene in ind2.chromosome])
    ind1_original_hash = ind1.hash
    ind2_original_hash = ind2.hash
    #logging.debug("Crossover; {} x {}".format(ind1.hash, ind2.hash))
    new_pairs = list()
    flip_signature = list()
    for pair in zip(ind1.chromosome, ind2.chromosome):
        pair = list(pair)        
        check = random.random()
        flg_flip = '0'
        if check <= indpb:
            #print(list(pair))
            pair.reverse()
            #print(list(pair).reverse())
            #new_pairs.append(list(pair).reverse())
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
        #logging.debug()
    
    return(ind1,ind2)
    #print([gene.index for gene in ind1.chromosome])
    #print([gene.index for gene in ind2.chromosome])    
    #raise Exception
    


# List of exported function names.
__all__ = []

# Deprecated functions
__all__.extend(['mj_list_flip'])