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

import logging
logging.basicConfig(level=logging.DEBUG)
#logging.debug("Started _main".format())
import csv
import sys, getopt
import os
from math import sqrt


def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

def read_vector(full_path_in):
    with open(full_path_in, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            vector = [float(item) for item in row]
    logging.debug("Vector: {}".format(vector))
    return(vector)

def zdt1(vector):
    g  = 1.0 + 9.0*sum(vector[1:])/(len(vector)-1)
    f1 = vector[0]
    f2 = g * (1 - sqrt(f1/g))
    return f1, f2
    
def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print("Incorrect command line arguments, need: -i <inputfile> -o <outputfile>")
        sys.exit(2)
    
    #print("Opts: {}".format(opts))
    #print("Args: {}".format(args))
    assert len(args) == 0, "Incorrect command line arguments, need: -i <inputfile> -o <outputfile>" 
    assert len(opts) == 2, "Incorrect command line arguments, need: -i <inputfile> -o <outputfile>" 

    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            relative_path_in = arg
        elif opt in ("-o", "--ofile"):
            relative_path_out = arg
        
    #relative_path_in = r'.\Input\testinput1'
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    full_path_in = os.path.join(cur_dir,relative_path_in)
    full_path_out = os.path.join(cur_dir,relative_path_out)
    
    logging.debug("Input file: {}".format(full_path_in))
    logging.debug("Output file: {}".format(full_path_out))
    
    vector = read_vector(full_path_in)

    result = zdt1(vector)



    with open(full_path_out, 'wb') as csvfile:
        this_writer = csv.writer(csvfile, delimiter=',')
        this_writer.writerow(result)
    logging.debug("Result: {} -> {}".format(result, full_path_out))

    
if __name__ == "__main__":
    main(sys.argv[1:])



