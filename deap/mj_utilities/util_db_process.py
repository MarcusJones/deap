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
        
def get_coverage(session):
    engine =session.bind 

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

def join_test():
    path_db = r"sqlite:///C:\ExportDir\DB\test.sql"
    engine = sa.create_engine(path_db, echo=0, listeners=[util_sa.ForeignKeysListener()])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    metadata = sa.MetaData()
    metadata.reflect(engine)    
        
    
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
    stmt = sa.select([generations_table]).select_from(j)
    
    j = sa.join(generations_table, results_table)
    stmt = sa.select([generations_table]).select_from(j)
    # NoForeignKeysError: Can't find any foreign key relationships between 'Generations' and 'Results'.
    
    
    print(stmt)

    #generations_table.join(results_table)
    
    
    
    #lister(fk)

def get_generations_list(session):
    engine =session.bind
    gen_table = util_sa.get_table_object(engine, "Generations")
    
    qry = sa.select(['*'],from_obj = gen_table)
    qry = sa.select([gen_table.c.gen],from_obj = gen_table)
    results = engine.execute(qry).fetchall()
    #gens = set(results)
    
    gens = [g[0] for g in results] 
    gens = list(set(gens))
    gens.sort()
    return(gens) 


def get_stats(session):
    gens = get_generations_list(session)
    
    get_generation_fitness(session,gens)

def asdf():
    j = join(user_table, address_table, user_table.c.id == address_table.c.user_id)
    stmt = select([user_table]).select_from(j)

def get_variable_names(session):
    engine =session.bind
    var_table = util_sa.get_table_object(engine, "Variables")
    
    qry = sa.select([var_table.c.name],from_obj = var_table)
    results = engine.execute(qry).fetchall()
    names = [name[0] for name in results]
    return names
    #gens = set(results)
      



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


def get_generation_fitness(session,gen):
    engine =session.bind
    gen_table = util_sa.get_table_object(engine, "Generations")
    results_table = util_sa.get_table_object(engine, "Results")
    
    print(results_table.c)
    
    #print_tables(session)
    #util_sa.printOnePrettyTable(engine,"Generations")
    #util_sa.printOnePrettyTable(engine,"Results")
    #print(gen_table)
    #print(gen_table[0])
    #print("gen_table.foreign_keys",gen_table.foreign_keys)
    #print("results_table.foreign_keys",results_table.foreign_keys)
    #print("results_table.columns",results_table.columns)
    #joined_table = gen_table.join(results_table)
    #q = session.query(gen_table).join(results_table)
    
    genres = sa.join(gen_table, results_table, gen_table.c.individual == results_table.c.hash)

    var_names = get_variable_names(session)
    var_joins = list()
    for name in var_names:
        this_vec_table = util_sa.get_table_object(engine, "vector_{}".format(name))
        col_name = 'var_c_'.format(name)
        #print(this_vec_table)
    
        j = sa.join(results_table,this_vec_table,results_table.c.var_c_var0 == this_vec_table.c.id)
        var_joins.append(j)
        print(j)
        #print(j.join(results_table.c.hash))
        #raise
    print(var_joins)
    raise
    stmt = sa.select().select_from(j)
    print(stmt)
    #qry = sa.select(['*'])

    #qry = qry.where(gen_table.c.individual == results_table.c.hash)

    results = engine.execute(stmt)
    lister(results)
    
    #print(results._metadata)
    
    rows = results.fetchall()
    col_names = results.keys()
    
    #df = pd.DataFrame()
    

    df = pd.DataFrame(data=rows, columns=col_names)
    df = df.set_index('id')
    print(df)
    #for row in results:
    #    print(row)
    

    #joined_table = results_table.join(gen_table)
    #results_table.join(gen_table)
    
    
    

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
        
        self.path_db = r"sqlite:///C:\ExportDir\DB\test.sql"
        self.engine = sa.create_engine(self.path_db, echo=0, listeners=[util_sa.ForeignKeysListener()])
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logging.debug("Initialized session {} with SQL alchemy version: {}".format(self.engine, sa.__version__))
        
    def test000(self):
        pass
        #join_test()
    def test000_coverage(self):
        print("**** TEST {} ****".format(whoami()))
        
        print_tables(self.session)

    def test010_coverage(self):
        print("**** TEST {} ****".format(whoami()))
        
        print('Coverage: {:0%}'.format(get_coverage(self.session)))
        
        
    def test015get_gen_list(self):
        get_generations_list(self.session)
            
    def test020_genstats(self):
        print("**** TEST {} ****".format(whoami()))
        
        get_stats(self.session)


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

