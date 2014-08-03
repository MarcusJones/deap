#===============================================================================
# Title of this Module
# Authors; MJones, Other
# 00 - 2012FEB05 - First commit
# 01 - 2012MAR17 - Update to ...
#===============================================================================

"""This module does A and B.
Etc.
"""

#===============================================================================
# Set up
#===============================================================================
# Standard:
from __future__ import division
from __future__ import print_function

import logging.config

from UtilityLogger import loggerCritical,loggerDebug
import utility_executor as util_exec
import deap.design_space as ds

#===============================================================================
# Code
#===============================================================================
def assert_valid(pop):
    for ind in pop:
        assert ind.fitness.valid, "{}".format(ind)

def get_results_hashes(session,Results):
   # metadata = sa.MetaData()
    #metadata.reflect(engine)    
    #return metadata
    #results_table = meta.tables["Results"]
    #meta = sa.MetaData()
    #meta.reflect(engine)
    #results_table = meta.tables["Results"]
    #qry = sa.select(results_table.c.hash)
    #res = engine.execute(qry).fetchall()
    #print(res)
    
    
    hashes = [row[0] for row in session.query(Results.hash).all()]
    return(hashes)
    
    

           
def assert_subset(pop1, pop2):
    pop1_hashes = set([ind.hash for ind in pop1])
    pop2_hashes = set([ind.hash for ind in pop2])
    assert(pop1_hashes <= pop2_hashes)



def printpoplist(pop, evolog, msg=None):
    hashes = [ind.hash for ind in pop]
    hashes.sort()
    
    print("{:20} {}".format(msg,hashes), file = evolog)
    #pass

def get_gen_evo_dict_entry(pop):
    hashes = [ind.hash for ind in pop]
    hashes.sort()
    return(hashes)

def printpop(msg, pop):
    print('*****************', msg)
    for ind in pop:
        print(ind)
        
        
def print_gen_dict(gd,gennum, path_evolog):
    
    with open(path_evolog, 'a') as evolog:
        print("Generation {}".format(gennum))
        
        print("{:17} {}".format('Start population',gd['Start population']), file=evolog)
        #print("{:17} {}".format('Population',gd['Population']), file = evolog)
        print("{:17} {}".format('Parents',gd['Selected parents']), file = evolog)
        print("{:17} {}".format('Mated offspring',gd['Mated offspring']), file = evolog)
        print("{:17} {}".format('Mutated offspring',gd['Mutated offspring']), file = evolog)
        print("{:17} {}".format('Combined',gd['Combined']), file = evolog)
        print("{:17} {}".format('Next',gd['Next population']), file = evolog)

def printhashes(pop, msg=""):
    hash_list = [ind.hash for ind in pop]
    print("{:>20} - {}".format(msg,sorted(hash_list)))


def filter_pop(pop,session,Results,mapping):
    """Divides pop into two;
    :returns: final_pop - Individuals already in Database, called back into existence by ORM
    :returns: eval_pop - Individuals not in Database
    """
    
    # final_pop is the resulting returned population
    final_pop = list()
    
    # eval_pop is the population which remains to be evaluated
    eval_pop = list()
    
    #===========================================================================
    # Get all matching from DB
    #===========================================================================
    pop_ids = [ind.hash for ind in pop]
    qry = session.query(Results).filter(Results.hash.in_(( pop_ids )))
    res = qry.all()
    
    # Assemble results into a dict
    results_dict = dict()
    for r in res:
        # Convert all in DB back to individuals
        this_ind = ds.convert_DB_individual(r,mapping)
        results_dict[r.hash] = this_ind
    
    
    #===========================================================================
    # Filter into final_pop and eval_pop
    #===========================================================================
    while pop:
        this_ind = pop.pop()
        if this_ind.hash in results_dict.keys():
            this_ind = results_dict[this_ind.hash]
            final_pop.append(this_ind)
        else:
            eval_pop.append(this_ind)
    
    # Ensure these are really valid
    for ind in final_pop:
        assert ind.fitness.valid, "{}".format(ind)
                
    logging.debug("EVALUATE {} individuals are already in database: {}".format(len(results_dict),sorted([i.hash for i in final_pop])))
    logging.debug("EVALUATE {} individuals are to be evaluated: {}".format(len(eval_pop),sorted([i.hash for i in eval_pop])))
    
    return final_pop, eval_pop 


def evaluate_pop(pop,session,Results,mapping,evaluate_func,settings):
    """evaluate_pop() performs a filter to ensure that each individual is only evaluated ONCE during the entire evolution
    evaluate_pop calls toolbox.evaluate(individual)
    - Entire population will be stored in final_pop list
    - If individual is already in DB, it is moved immediately into final_pop (recreated by ORM)
    - If not in DB, the individual is evaluated and stored in a dictionary newly_evald and added to final_pop
    - DUPLICATE HANDLING: If the individual is already existing in newly_evald, it is not re-evaluated, but added directly to final_pop
    - final_pop is returned by function
    """
    logging.debug("EVALUATE population size {}: {}".format(len(pop),sorted([i.hash for i in pop])))
    eval_count = 0
    
    final_pop, eval_pop = filter_pop(pop,session,Results,mapping)
    
    with loggerDebug():
        # Only evaluate each individual ONCE
        newly_evald = dict()
        while eval_pop:
            ind = eval_pop.pop()
            # Check if it has been recently evaluated
            if ind.hash in newly_evald.keys():
                logging.debug("Recently evaluated: {} ".format(newly_evald[ind.hash]))
                copy_ind = newly_evald[ind.hash]
                assert(copy_ind.fitness.valid)
                final_pop.append(copy_ind)
                # Skip to next 
                continue
            else:
                # Individual not recently eval'd (not in dict)
                # This individual needs to be evaluated
                #pass
            
                # Do a fresh evaluation
                #with loggerCritical():
                with loggerDebug():
                    logging.debug("Fresh eval: {} ".format(ind.hash))
                    ind = evaluate_func(settings,ind)
                    logging.debug("Newly evaluated {}".format(ind.hash))
                    
                assert(ind.fitness.valid)
                eval_count += 1
                res = ds.convert_individual_DB(Results,ind)
                newly_evald[res.hash] = ind
                session.merge(res)
                final_pop.append(ind)
    session.commit()

    # Assert that they are indeed evaluated
    for ind in final_pop:
        assert ind.fitness.valid, "{}".format(ind)
        
    return final_pop, eval_count


def evaluate_pop_parallel(pop,session,Results,mapping,evaluate_func,settings):
    """
    """
    logging.debug("EVALUATE population size {}: {}".format(len(pop),sorted([i.hash for i in pop])))
    eval_count = 0
    
    final_pop = list()
    eval_pop = list()
    
    pop_ids = [ind.hash for ind in pop]
    
    # Get all matching from DB
    qry = session.query(Results).filter(Results.hash.in_(( pop_ids )))
    res = qry.all()
    
    # Assemble results into a dict
    results_dict = dict()
    for r in res:
        this_ind = ds.convert_DB_individual(r,mapping)
        results_dict[r.hash] = this_ind
    
    while pop:
        this_ind = pop.pop()
        #try: 
        if this_ind.hash in results_dict.keys():
            this_ind = results_dict[this_ind.hash]
            final_pop.append(this_ind)
        else:
        #except KeyError:
            eval_pop.append(this_ind)
    
    for ind in final_pop:
        if not ind.fitness.valid:
            print(ind)
            util_sa.printOnePrettyTable(session.bind, 'Results',maxRows = None)
            raise Exception("Invalid fitness from DB")
        #assert ind.fitness.valid, "{}".format(ind)
                
    logging.debug("EVALUATE {} individuals are already in database: {}".format(len(results_dict),sorted([i.hash for i in final_pop])))
    logging.debug("EVALUATE {} individuals are to be evaluated: {}".format(len(eval_pop),sorted([i.hash for i in eval_pop])))
    
    
    with loggerDebug():
        # Only evaluate each individual ONCE
        newly_evald = dict()
        pool = list()
        eval_pop_set = list(set(eval_pop))
        while eval_pop_set:
            ind = eval_pop_set.pop()
            # Check if it has been recently evaluated
            if ind.hash in newly_evald.keys():
                logging.debug("Recently evaluated: {} ".format(newly_evald[ind.hash]))
                copy_ind = newly_evald[ind.hash]
                assert(copy_ind.fitness.valid)
                final_pop.append(copy_ind)
                # Skip to next
                continue
            else:
                # Individual not recently eval'd (not in dict)
                # This individual needs to be evaluated
                # Add to pool
                with loggerDebug():
                    ind = evaluate_func(settings,ind)
                    pool.append(ind)
        
        
        commands = [ind.cmd for ind in pool]
        
        #for ind in pool:
        #    print(ind.directory,ind.cmd)
        util_exec.execute_parallel(commands)
        raise
        eval_count += 1
        res = ds.convert_individual_DB(Results,ind)
        newly_evald[res.hash] = ind

        final_pop.append(ind)
        session.merge(res)                
        
    session.commit()

    # Assert that they are indeed evaluated
    for ind in final_pop:
        assert ind.fitness.valid, "{}".format(ind)
        
    return final_pop, eval_count

