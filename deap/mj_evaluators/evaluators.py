
#import random
#from math import sin, cos, pi, exp, e, sqrt
#from operator import mul
#from functools import reduce
#from decimal import Decimal
import logging
import os
import shutil
import utility_file as util_file

def mj_zdt1_decimal(settings,individual):
    """ZDT1 multiobjective function.
    
    :math:`g(\\mathbf{x}) = 1 + \\frac{9}{n-1}\\sum_{i=2}^n x_i`
    
    :math:`f_{\\text{ZDT1}1}(\\mathbf{x}) = x_1`
    
    :math:`f_{\\text{ZDT1}2}(\\mathbf{x}) = g(\\mathbf{x})\\left[1 - \\sqrt{\\frac{x_1}{g(\\mathbf{x})}}\\right]`
    """
    values = list(individual[:])
    #print(values)
    #raise
    #val = values[0]
    #print(val)
    #print(type(val))
    #print(type(val.value))
    
    #raise
    #print(values)
    try:
        values = [float(val.value) for val in values]
    except AttributeError:
        pass
    #values = [float(str(val.value)) for val in values]
    #print(values)
    #print(type(values[0]))
    #print(type(values[0].value))
    #print(float(values[0].value))
    #raise
    #individual[:] = values
    #print(individual)
    #raise
    g  = 1.0 + 9.0*sum(values[1:])/(len(values)-1)
    f1 = values[0]
    f2 = g * (1 - sqrt(f1/g))
    
    #this_fit = individual.fitness
    individual.fitness.setValues((f1, f2))
    #print(this_fit)
    #individual.fitness = this_fit
    #raise Exception
    #individual.fitness.values = (f1, f2)
    
    logging.debug("Evaluated {} -> {}".format(values, individual.fitness))
    
    return individual




def mj_zdt1_decimal_exe(settings,individual):
    #===========================================================================
    # Check paths
    #===========================================================================
    assert os.path.exists(settings['path_exe']), "EXE does not exist"
    assert os.path.exists(settings['path_template']), "Template does not exist"
    
    for k,v, in settings.iteritems():
        print("{:>30} : {:<100} {}".format(k,v, type(v)))
    
    this_ind_sub_dir = os.path.join(settings['run_full_path'],"individuals","{}".format(individual.hash))
    #print(this_ind_sub_dir)
    os.makedirs(this_ind_sub_dir)
    
    path_input_file = os.path.join(this_ind_sub_dir,'input.txt')
    path_output_file = os.path.join(this_ind_sub_dir,'output.txt')
    
    shutil.copy(settings['path_template'], path_input_file)
    #raise 
    exe_str = "{} -i {} -o {}".format(settings['path_exe'], path_input_file, path_output_file)
    
    #===========================================================================
    # Apply changes
    #===========================================================================
    input_file_obj = util_file.FileObject(path_input_file)
    #print(individual)
    
    replacements = list()
    for allele in individual.chromosome:
        find_val = "{}{}".format(settings['replace_sigil'],allele.name)
        repl_val = allele.value
        replacements.append([find_val,repl_val])
        
    print(replacements)
    
    input_file_obj.makeReplacements(replacements)
        #print(allele.name, )
        #print(allele) 
    input_file_obj.writeFile(input_file_obj.filePath)
    
    individual.directory = this_ind_sub_dir
    individual.cmd = exe_str
    #individual.sub_dir = os.path.join(settings['run_full_path'],"individuals","{}".format(individual.hash))
    #print(individual.sub_dir)
    return individual