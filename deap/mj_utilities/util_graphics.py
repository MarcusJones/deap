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
import unittest

from utility_inspect import whoami, whosdaddy, listObject


import numpy as np
import matplotlib

import matplotlib.pyplot as plt
import matplotlib as mpl
print(mpl.backends.backend)
matplotlib.rcParams['backend'] = "TkAgg"
print(mpl.backends.backend)

#===============================================================================
# Code
#===============================================================================
def print_res(pop, optimal_front, outpath = r'C:\\ExportDir\\out.pdf' ):
    optimal_front = np.array(optimal_front)
    front = np.array([ind.fitness.values for ind in pop])
    plt.scatter(optimal_front[:,0], optimal_front[:,1], c="r")
    #print(front)
    plt.scatter(front[:,0], front[:,1], c="b")
    plt.axis("tight")
    #plt.savefig('C:\ExportDir\test1.png')
    #plt.show()
    plt.savefig(outpath, transparent=True, bbox_inches='tight', pad_inches=0)

#===============================================================================
# Main
#===============================================================================
if __name__ == "__main__":
    print(ABSOLUTE_LOGGING_PATH)
    logging.config.fileConfig(ABSOLUTE_LOGGING_PATH)


    myLogger = logging.getLogger()
    myLogger.setLevel("DEBUG")

    logging.debug("Started _main".format())

    #print FREELANCE_DIR

    unittest.main()

    logging.debug("Finished _main".format())
