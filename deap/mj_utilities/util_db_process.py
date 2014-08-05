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

import design_space as ds

import scipy.io as sio

def lister(item):
    for i in dir(item):
        print("{:>40} - {}".format(item, i))

#===============================================================================
# Code
#===============================================================================

#--- Utility

def print_tables(session):
    engine =session.bind 
    
    table_names = util_sa.get_table_names(engine)
    for name in table_names:
        this_table = util_sa.get_table_object(engine, name)
        print(this_table)
        print(this_table.foreign_keys)

def write_frame_matlab(frame,path,name = 'df'):
    mdict = {}

    # First get the index from the pandas frame as a regular datetime
    index = np.array(frame.index.values)

    mdict['index'] = index
    mdict['data'] = frame.values

    # Header come as a list of tuples
    headers = frame.columns.values
    if len(headers.shape) == 1:
        mdict['headers'] = np.array([headers], dtype=np.object)
    
    elif len(headers.shape) == 2:
        # Convert to a true 2D list for numpy
        headers = [list(item) for item in headers]
        headers = np.array(headers, dtype=np.object)

        mdict['headers'] = headers

    
    if len(frame.columns.names) > 1:
        mdict['headerDef'] = np.array(frame.columns.names, dtype = np.object)
    else:
        mdict['headerDef'] = np.array('Header', dtype = np.object)
    
    sio.savemat(path, {name: mdict})

    logging.debug("Saved frame {} to {}".format(frame.shape, path))


#--- Simple queries and DataFrames
        
def get_coverage(meta):
    """Divide number of evaluations by Cardinality of DesignSpace
    """
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


def get_variable_names(meta):
    """List of variable names
    """        
    engine = meta.bind
    var_table = meta.tables["Variables"]
    
    qry = sa.select([var_table.c.name],from_obj = var_table)
    results = engine.execute(qry).fetchall()
    names = [name[0] for name in results]
    return names

def get_objective_names(meta):
    """List of objective names
    """    
    engine = meta.bind
    obj_table = meta.tables["Objectives"]
    
    qry = sa.select([obj_table.c.name],from_obj = obj_table)
    results = engine.execute(qry).fetchall()
    names = [name[0] for name in results]
    return names

def get_generations_list(meta):
    """List of generation numbers
    """
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



#--- Complex queries and DataFrames
def get_all_gen_stats_df(meta):
    """Loop over all generations, return summary stats DF
    """
    logging.debug("Calculating statistics".format())
    
    stats = dict()
    
    gennums = get_generations_list(meta)
     
    #stat = list()
    df_mean = list()
    df_std = list()
    df_max = list()
    df_min = list()
    for num in gennums:
        df = get_one_gen_stats_df(meta,num)
        #stats_df['mean'] = df.mean() 
        df_mean.append(df.mean())
        df_std.append(df.std())
        df_max.append(df.max())
        df_min.append(df.min())
        
    stats['mean'] = pd.concat(df_mean, axis = 1).T
    stats['std'] = pd.concat(df_std, axis = 1).T
    stats['min'] = pd.concat(df_min, axis = 1).T
    stats['max'] = pd.concat(df_max, axis = 1).T

    
    return(stats)

def get_one_gen_stats_df(meta,gennum):
    """Get DF from GENERATIONS join RESULTS for gennum
    """
    engine = meta.bind
    qry = get_generations_qry(meta)
    qry = qry.where("Generations.gen == {}".format(gennum))
    
    obj_cols = list()
    for name in get_objective_names(meta):
        obj_cols.append("Results_obj_c_{}".format(name))
        
    
    res = engine.execute(qry)
    
    rows = res.fetchall()
    col_names = res.keys()
    
    df = pd.DataFrame(data=rows, columns=col_names)
    df = df[obj_cols]
    logging.debug("Statistics for generation {}".format(gennum))
    return df


def get_results_df(meta):
    """Generate DF and SQL query returning 
    RESULTS join *VECTORS"""    
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

    def convert_dt_str(dtime64):
        date_as_string = str(dtime64)
        #year_as_string = date_in_some_format[-4:] # last four characters
        return date_as_string
    
    df['Results_start'] = df['Results_start'].apply(convert_dt_str)
    df['Results_finish'] = df['Results_finish'].apply(convert_dt_str)
    #print(df)
    #raise
    for name in get_variable_names(meta):
        df.drop(['vector_{}_id'.format(name)], axis=1, inplace=True)
        df.drop(['Results_var_c_{}'.format(name)], axis=1, inplace=True)
        df.rename(columns={'vector_{}_value'.format(name): name}, inplace=True)
    for name in get_objective_names(meta):
        df.rename(columns={'Results_obj_c_{}'.format(name): name}, inplace=True)
    
    df.rename(columns={'Results_hash'.format(): 'individual'}, inplace=True)
    logging.debug("Results table returned as frame")

    return df

def get_generations_qry(meta):
    """Generate SQL query returning 
    GENERATIONS join RESULTS join *VECTORS"""
    
    
    gen_table = meta.tables["Generations"]
    results_table = meta.tables["Results"]

    qry = gen_table.join(results_table)
    
    # Join each variable dynamically
    for name in get_variable_names(meta):
        this_vec_table = meta.tables["vector_{}".format(name)]
        qry = qry.join(this_vec_table)
    
    qry = qry.select(use_labels=True)
    
    return qry

def get_generations_qry_ospace_only(meta):
    """Generate SQL query returning 
    GENERATIONS join RESULTS"""    
    gen_table = meta.tables["Generations"]
    results_table = meta.tables["Results"]

    qry = gen_table.join(results_table)
    
    qry = qry.select(use_labels=True)
    
    return qry


def get_generations_df(meta):
    """Generate DataFrame from
    GENERATIONS join RESULTS join *VECTORS
    """
    
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


def get_generations_Ospace_df(meta):
    """Generate DataFrame from
    GENERATIONS join RESULTS
    """
        
    engine = meta.bind
    
    qry = get_generations_qry_ospace_only(meta)
    results = engine.execute(qry)
    
    rows = results.fetchall()
    col_names = results.keys()
    
    # Drop ID columns as well
    df = pd.DataFrame(data=rows, columns=col_names)
    df = df.set_index('Generations_id')
    df.drop(['Results_hash', 'Results_start','Results_finish'], axis=1, inplace=True)
    for name in get_variable_names(meta):
        df.drop(['Results_var_c_{}'.format(name)], axis=1, inplace=True)
        df.rename(columns={'vector_{}_value'.format(name): name}, inplace=True)
    for name in get_objective_names(meta):
        df.rename(columns={'Results_obj_c_{}'.format(name): name}, inplace=True)
    
    df.rename(columns={'Generations_individual'.format(): 'individual'}, inplace=True)
    
    logging.debug("Generations table returned as frame")
    
    return df


#--- Get all stats and write to path
def process_db_to_mat(path_db,path_output):
    """Write
    -Results 
    -Generations
    -Stats
    """
    
    path_db = r"sqlite:///" + path_db
    engine = sa.create_engine(path_db, echo=0, listeners=[util_sa.ForeignKeysListener()])
    meta = sa.MetaData(bind = engine)
    meta.reflect()
    
    #===========================================================================
    # Results dump
    #===========================================================================
    df = get_results_df(meta)
    name = 'results'
    path = os.path.join(path_output,"{}.mat".format(name))
    write_frame_matlab(df,path,name)
    
    #===========================================================================
    # Generations and objectives
    #===========================================================================
    df = get_generations_Ospace_df(meta)
    name = 'generations'
    path = os.path.join(path_output,"{}.mat".format(name))
    write_frame_matlab(df,path,name)

    
    #===========================================================================
    # Statistics on generations
    #===========================================================================
    stats = get_all_gen_stats_df(meta)
    for name,df in stats.iteritems():
        path = os.path.join(path_output,"{}.mat".format(name))
        #path = r"c:\ExportDir\Mat\{}.mat".format(name)
        #print(name,v)
        #(frame,path,name = name)
        write_frame_matlab(df,path,name)    


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
        print("Results")
        print(res)
        
        gens = get_generations_df(self.meta)
        print("Generations")
        print(gens)
    
    def test030_get_write_ospace(self):
        df = get_generations_Ospace_df(self.meta)
        #print(df)
        name = 'generations'
        path = r"c:\ExportDir\Mat\{}.mat".format(name)
        write_frame_matlab(df,path,name)
        
    def test040_get_write_stats(self):
        print("**** TEST {} ****".format(whoami()))
        stats = get_all_gen_stats_df(self.meta)
        
        for name,df in stats.iteritems():
            path = r"c:\ExportDir\Mat\{}.mat".format(name)
            #print(name,v)
            #(frame,path,name = name)
            write_frame_matlab(df,path,name)



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

