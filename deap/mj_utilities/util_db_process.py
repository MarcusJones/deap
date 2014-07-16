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

from utility_inspect import whoami, whosdaddy, listObject
import utility_SQL_alchemy as util_sa
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import numpy as np

import deap.design_space as ds


#===============================================================================
# Code
#===============================================================================
def get_coverage(session):
    print(session)
    
    query = session.query(ds.Generation)#.filter(ds.Results.hash == ind.hash)
    res = query.all()
    for r in res:
        print(r)    
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
    objTable = util_sa.getTableObject(metadata, "objectives")

    s = sa.select([objTable.c.description])

    objNames = ['"{}"'.format(objName[0]) for objName in engine.execute(s)]

    genTable = util_sa.getTableObject(metadata, "generations")

    resultsTable = util_sa.getTableObject(metadata, "results")

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
    genTable = util_sa.getTableObject(metadata, "generations")

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
        self.engine = sa.create_engine(self.path_db, echo=0)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logging.debug("Initialized session {} with SQL alchemy version: {}".format(self.engine, sa.__version__))

    def test010_Load(self):
        print("**** TEST {} ****".format(whoami()))
        
        get_coverage(self.session)
        
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

