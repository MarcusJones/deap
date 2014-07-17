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

from config import *

import logging.config
logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
myLogger = logging.getLogger()
myLogger.setLevel("DEBUG")
import unittest

import pandas as pd

import utility_path as util_path
from utility_inspect import whoami, whosdaddy, listObject
import utility_SQL_alchemy as util_sa
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import numpy as np

import deap.design_space as ds


def lister(item):
    for i in dir(item):
        print("{:>40} - {}".format(item, i))

#===============================================================================
# Code
#===============================================================================
def print_tables(session):
    engine =session.bind 
    
    table_names = util_sa.get_table_names(engine)
    for name in table_names:
        this_table = util_sa.get_table_object(engine, name)
        print(this_table)
        print(this_table.foreign_keys)
        
def get_coverage(meta):
    engine =meta.bind 

    # Get number of rows
    results_table = util_sa.get_table_object(engine, "Results")
    num_res = util_sa.get_number_records(engine,results_table)
    
    
    # Partially reassemble the mapping
    var_table = util_sa.get_table_object(engine, "Variables") 
    var_rows = util_sa.get_dict(engine,var_table)
    
    cardinality = 1
    for row in var_rows:
        vector_table_name = "vector_{}".format(row['name'])
        vector_table = util_sa.get_table_object(engine, vector_table_name)
        len_vec = util_sa.get_number_records(engine,vector_table)
        #print(vector_table_name, len_vec)
        #cardinality = cardinality * len_vec
        cardinality *= len_vec
        #print(vector_table_name)
    logging.debug("{} evaluations out of a cardinality {} designspace".format(num_res,cardinality))
    return num_res/cardinality

def join_test(meta):
    #metadata = sa.MetaData(bind=engine)
    #metadata.reflect()
     
    print(meta)
    gen_table = meta.tables["Generations"]
    results_table = meta.tables["Results"]
    print(results_table.c)
    print(gen_table.c)    
    qry = gen_table.join(results_table)
    
    print(qry.select())
    
    print(meta.bind)
    raise

    #metadata = sa.MetaData()
    #metadata.reflect(engine)    
    

    generations_table = metadata.tables['Generations']
    print(generations_table.columns) 
    # ['Generations.id', 'Generations.gen', 'Generations.individual']
    
    results_table = metadata.tables['Results']
    print(results_table.columns)
    # ['Results.hash', 'Results.start', 'Results.finish', 'Results.var_c_var0', 'Results.var_c_var1', 'Results.obj_c_obj1', 'Results.obj_c_obj2']
    
    print("gens_table.foreign_keys",generations_table.foreign_keys)
    # gens_table.foreign_keys set([ForeignKey(u'Results.hash')])
    fk = generations_table.foreign_keys.pop()
    print("fk.column",fk.column)
    # fk.column Results.hash
    print("fk.parent",fk.parent)
    # fk.parent Generations.individual
    
    
    j = sa.join(generations_table, results_table, generations_table.c.individual == results_table.c.hash)
    #j = j.join()
    stmt = sa.select([generations_table]).select_from(j)
    
    j = sa.join(generations_table, results_table)
    stmt = sa.select([generations_table]).select_from(j)
    # NoForeignKeysError: Can't find any foreign key relationships between 'Generations' and 'Results'.
    
    
    print(stmt)

    #generations_table.join(results_table)
    
    
    
    #lister(fk)



#--- Utility
def get_variable_names(meta):
    engine = meta.bind
    var_table = meta.tables["Variables"]
    
    qry = sa.select([var_table.c.name],from_obj = var_table)
    results = engine.execute(qry).fetchall()
    names = [name[0] for name in results]
    return names

def get_objective_names(meta):
    engine = meta.bind
    obj_table = meta.tables["Objectives"]
    
    qry = sa.select([obj_table.c.name],from_obj = obj_table)
    results = engine.execute(qry).fetchall()
    names = [name[0] for name in results]
    return names
def get_generations_list(meta):
    engine = meta.bind
    gen_table = meta.tables["Generations"] 
    #util_sa.get_table_object(engine, "Generations")
    
    qry = sa.select(['*'],from_obj = gen_table)
    
    qry = sa.select([gen_table.c.gen],from_obj = gen_table)
    results = engine.execute(qry).fetchall()
    #gens = set(results)
    
    gens = [g[0] for g in results] 
    gens = list(set(gens))
    gens.sort()
    return(gens) 



#--- Get dfs

def get_stats_df(meta):
    engine = meta.bind
    gennums = get_generations_list(meta)
    qry = get_generations_qry(meta)
    qry = qry.where("Generations.gen == 0")
    
    results = engine.execute(qry)
    
    rows = results.fetchall()
    print(rows)
    raise


def get_results_df(meta):
    engine = meta.bind
    results_table = meta.tables["Results"]

    
    qry = results_table
    
    # Join each variable dynamically
    for name in get_variable_names(meta):
        this_vec_table = meta.tables["vector_{}".format(name)]
        qry = qry.join(this_vec_table)
    
    qry = qry.select(use_labels=True)
    
    results = engine.execute(qry)
    
    rows = results.fetchall()
    col_names = results.keys()
    
    # Drop ID columns as well
    df = pd.DataFrame(data=rows, columns=col_names)
    df.drop(['Results_start','Results_finish'], axis=1, inplace=True)
    for name in get_variable_names(meta):
        df.drop(['vector_{}_id'.format(name)], axis=1, inplace=True)
        df.drop(['Results_var_c_{}'.format(name)], axis=1, inplace=True)
        df.rename(columns={'vector_{}_value'.format(name): name}, inplace=True)
    for name in get_objective_names(meta):
        df.rename(columns={'Results_obj_c_{}'.format(name): name}, inplace=True)
    
    df.rename(columns={'Results_hash'.format(): 'individual'}, inplace=True)
    

    return df

def get_generations_qry(meta):
    gen_table = meta.tables["Generations"]
    results_table = meta.tables["Results"]

    qry = gen_table.join(results_table)
    
    # Join each variable dynamically
    for name in get_variable_names(meta):
        this_vec_table = meta.tables["vector_{}".format(name)]
        qry = qry.join(this_vec_table)
    
    qry = qry.select(use_labels=True)
    
    return qry

def get_generations_df(meta):
    engine = meta.bind
    
    qry = get_generations_qry(meta)
    results = engine.execute(qry)
    
    rows = results.fetchall()
    col_names = results.keys()
    
    # Drop ID columns as well
    df = pd.DataFrame(data=rows, columns=col_names)
    df = df.set_index('Generations_id')
    df.drop(['Results_hash', 'Results_start','Results_finish'], axis=1, inplace=True)
    for name in get_variable_names(meta):
        df.drop(['vector_{}_id'.format(name)], axis=1, inplace=True)
        df.drop(['Results_var_c_{}'.format(name)], axis=1, inplace=True)
        df.rename(columns={'vector_{}_value'.format(name): name}, inplace=True)
    for name in get_objective_names(meta):
        df.rename(columns={'Results_obj_c_{}'.format(name): name}, inplace=True)
    
    df.rename(columns={'Generations_individual'.format(): 'individual'}, inplace=True)
    
    return df


#--- OLD
def old(session):
    table_names = util_sa.get_table_names(engine)
    print(table_names)    
    var_table = util_sa.get_table_object(engine, "Results")
    print(var_table)
    lister(var_table)
    print(var_table.foreign_keys)
    raise
    var_rows = util_sa.get_dict(engine, var_table)
    print(var_rows)
        
    print(session)
    print(dir(session))
    #util_sa.get_table_names(engine)
    engine =session.bind 
    table_names = util_sa.get_table_names(engine)

    var_table = util_sa.get_table_object(engine, "Variables")  
    var_rows = util_sa.get_dict(engine, var_table)
    print(var_rows)
    
    print(table_names)  
    query = session.query(ds.Generation)#.filter(ds.Results.hash == ind.hash)
    res = query.all()
#     for r in res:
#         print(r)


def compile_query(query):
    raise
    from sqlalchemy.sql import compiler
    from psycopg2.extensions import adapt as sqlescape
    # or use the appropiate escape function from your db driver

    dialect = query.session.bind.dialect
    statement = query.statement
    comp = compiler.SQLCompiler(dialect, statement)
    comp.compile()
    enc = dialect.encoding
    params = {}
    for k,v in comp.params.iteritems():
        if isinstance(v, unicode):
            v = v.encode(enc)
        params[k] = sqlescape(v)
    return (comp.string.encode(enc) % params).decode(enc)


            
    pass
def get_gen_stats(engine,genNum):
    """Get the statistics for one generation
    "genNum"
    "names" - Order of the objectives
    "avg" - One average fitness for the first, second, N objective
    "max" -
    "min" -
    """
    # --- Objectives
    # Get the objective column names
    
    metadata = util_sa.get_metadata(engine)
    objTable = util_sa.get_table_object(metadata, "objectives")

    s = sa.select([objTable.c.description])

    objNames = ['"{}"'.format(objName[0]) for objName in engine.execute(s)]

    genTable = util_sa.get_table_object(metadata, "generations")

    resultsTable = util_sa.get_table_object(metadata, "results")

    joinedTable = genTable.join(resultsTable)

    qry = sa.select(objNames, from_obj=joinedTable )

    qry = qry.where(genTable.c.generation == genNum)

    results = engine.execute(qry)

    resultsLabels = results._metadata.keys


    resultsTuples = results.fetchall()


    results = {
               "genNum" : genNum,
               "names"  : objNames,
               "avg"    : np.mean(resultsTuples,0),
               "max"    : np.max(resultsTuples,0),
               "min"    : np.min(resultsTuples,0),
               }


    return results

def get_run_stats(engine):
    metadata = util_sa.get_metadata(engine)
    genTable = util_sa.get_table_object(metadata, "generations")

    qry = sa.select([genTable.c.generation], from_obj = genTable)
    qry = qry.order_by(sa.desc(genTable.c.generation))

    numGens = engine.execute(qry).first()[0]

    results = {"genNum"     : list(),
               "min"        : list(),
               "avg"        : list(),
               "max"        : list(),
               "names"      : None,
               }
    genNumCols = list()

    for genNum in range(numGens):
        genStat = get_gen_stats(engine,genNum)
        #print(genStat)
        results["genNum"].append(genNum)
        results["min"].append([float(val) for val in genStat["min"]])
        results["avg"].append([float(val) for val in genStat["avg"]])
        results["max"].append([float(val) for val in genStat["max"]])
    results["names"] = genStat["names"]

    return results

#===============================================================================
# Unit testing
#===============================================================================

class allTests(unittest.TestCase):

    def setUp(self):
        print("**** TEST {} ****".format(whoami()))
        
        path_db = r"sqlite:///C:\ExportDir\DB\test.sql"
        engine = sa.create_engine(path_db, echo=0, listeners=[util_sa.ForeignKeysListener()])
        meta = sa.MetaData(bind = engine)
        meta.reflect()
        self.meta = meta
        
    def test000_print_tables(self):
        print("**** TEST {} ****".format(whoami()))
        print_tables(self.meta)

    def test010_coverage(self):
        print("**** TEST {} ****".format(whoami()))
        print('Coverage: {:0%}'.format(get_coverage(self.meta)))
        
    def test015_get_gen_list(self):
        gens = get_generations_list(self.meta)
        print(gens)
        
    def test020_get_dfs(self):
        print("**** TEST {} ****".format(whoami()))

        
        res = get_results_df(self.meta)
        print(res)
        
        gens = get_generations_df(self.meta)
        print(gens)
        
    def test030_get_stats(self):
        print("**** TEST {} ****".format(whoami()))

        get_stats_df(self.meta)      


#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(ABSOLUTE_LOGGING_PATH)
    #logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)
    #myLogger = logging.getLogger()
    #myLogger.setLevel("DEBUG")

    #logging.debug("Started _main".format())

    #unittest.main()

    #logging.debug("Finished _main".format())

