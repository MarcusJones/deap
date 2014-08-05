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
from deap import design_space as ds
import time
import psutil


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


def eval_parallel(eval_pop, settings):

    pending_queue = eval_pop
    live_queue = list()
    finished_queue = list()
    
    start_time = time.time()
    
    while live_queue or pending_queue:
        # The system loop delay
        time.sleep(settings['parallel_delay'])
        
        # Check CPU load
        currentCPU = psutil.cpu_percent()
        
        elapsed_time = time.time() - start_time
        
        if elapsed_time % 10 == 1:
            
  
            #print(elapsed_time)
            logging.debug("{} seconds Pending: {}, Running: {}, Finished: {}, CPU: {}%".format(
                                                                                               elapsed_time,
                                                                 len(pending_queue),
                                                                 len(live_queue),
                                                                 len(finished_queue),
                                                                 currentCPU
                                                                 ))
                     
        # Try to move 1 process from pending -> live
        if (pending_queue and
            currentCPU <= settings['Maximum_CPU'] and 
            len(live_queue) < settings['Maximum_processes']):
            
            # Shift a run to the live_queue
            this_ind = pending_queue.pop()
            
            this_ind.run_status = "Running"
            
            live_queue.append(this_ind)
            
            # Execute this run (the last one in live_queue)
            with loggerCritical():
                live_queue[-1].pre_process(settings)
                live_queue[-1].execute(settings)

        # Check the live queue
        for ind in live_queue:
            ind.update()
            #logging.debug("Updated {}, status: {}".format(ind.hash,ind.run_status))                
            # Move off the live queue if finished
            if ind.run_status == "Finished":
                #logging.debug("Moving {} off into finished".format(ind.hash))
                finished_queue.append(ind)
                live_queue.remove(ind)
                ind.post_process(settings)
    
    return finished_queue


def eval_unique_pop(eval_pop, settings):
    """Evaluate the population according to the settings
    """
    
    #===========================================================================
    # Parallel
    #===========================================================================
    if 'execution' in settings.keys() and settings['execution'] == 'parallel':
        for ind in eval_pop:
            ind.run_status = 'Pending'
            
        with loggerCritical():
            eval_pop = eval_parallel(eval_pop, settings)
        
    #===========================================================================
    # Serial
    #===========================================================================
    else:
        for ind in eval_pop:
            with loggerDebug():
                ind.pre_process(settings)
                ind.execute(settings)
                ind.post_process(settings)
                
    for ind in eval_pop:
        assert ind.fitness.valid, "Individual {} has invalid fitness; {}".format(ind.hash, ind.fitness)
    
    logging.debug("Evaluated {} unique individuals".format(len(eval_pop)))
    
    return eval_pop
        
def run_population(eval_pop,settings):
    """Given a population, call the .execute() method on each individual
    The .execute() method adds the fitness to each ind
    :returns: Evaluated pop with valid fitness
    """

    
    #===========================================================================
    # To ensure only unique evaluations, get only unique individuals 
    #===========================================================================
    unique_evals = list(set(eval_pop))
    
    logging.debug("Evaluating {} unique individuals from population of {}".format(len(unique_evals),len(eval_pop))) 


    #===========================================================================
    # Evaluate
    #===========================================================================
    unique_evals = eval_unique_pop(unique_evals, settings)

    #===========================================================================
    # Rebuild the original population by copying for each in original pop
    #===========================================================================
    # Create a dict to reference newly evaluated individuals
    eval_pop_dict = dict([(ind.hash, ind) for ind in unique_evals])
    
    # The original pop signaure
    original_hashes = [ind.hash for ind in eval_pop]
    
    # For each in original, copy to final_pop
    final_pop = list()
    for ihash in original_hashes:
        copy_ind = eval_pop_dict[ihash]
        assert(copy_ind.fitness.valid)
        final_pop.append(copy_ind)
    
    #raise

    return final_pop

def evaluate_pop(pop,session,Results,mapping,settings):
    """evaluate_pop() 
    First performs a filter against individuals already in database
    Then evaluates remaining unique individuals
    New individuals are added to database
    These new evaluations are appended to final_pop and returned
    """
    logging.debug("EVALUATE population size {}: {}".format(len(pop),sorted([i.hash for i in pop])))
    eval_count = 0
    
    # Individuals already in database are added directly to population
    final_pop, eval_pop = filter_pop(pop,session,Results,mapping)
    
    # Remaining individuals are evaluated
    evaluated_pop = run_population(eval_pop,settings)

    # Newly evaluated individuals are added to Database
    for ind in evaluated_pop:
        res = ds.convert_individual_DB(Results,ind)
        session.merge(res)
        final_pop.append(ind)
        
    session.commit()
    
    # Assert that they are indeed evaluated
    for ind in final_pop:
        assert ind.fitness.valid, "{}".format(ind)

    return final_pop, eval_count


def evaluate_pop_parallelOLD(pop,session,Results,mapping,evaluate_func,settings):
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

