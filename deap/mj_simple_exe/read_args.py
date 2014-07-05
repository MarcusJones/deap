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

import sys, getopt

def main(argv):
    inputfile = ''
    outputfile = ''
    
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('Unrecognized input')
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
        
    logging.debug("Opts {}".format(opts))
    logging.debug("Args {}".format(args))
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        
    print('Input file is {}'.format(inputfile))
    print('Output file is {}'.format(outputfile))

if __name__ == "__main__":
   main(sys.argv[1:])



