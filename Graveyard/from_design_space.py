
def evaluate_population(population, engine):
    raise
    """Given a list of individuals, evaluate only those which are
    1. Unique
    2. Not already existing in database
    """
    logging.info("Evaluating {} individuals, typical: {}".format(len(population),population[0]))

    unique_pop = list(set(population))
    logging.info("Of these {} individuals, {} are unique".format(len(population),len(unique_pop)))

    # Get metadata
    metadata = sa.MetaData()
    metadata.reflect(engine)

    # Get all tables
    #util_sa.print_all_pretty_tables(engine)
    results_table =  metadata.tables['results']
    objectives_table = metadata.tables['objectives']

    # Get objective names
    #objectives_table.fetchall()
    objective_names = util_sa.get_rows(engine,objectives_table)
    objective_names = [row[1] for row in objective_names]
    #logging.info("Objectives: {}".format(objective_names))

    objective_columns = [results_table.c[obj_name] for obj_name in objective_names]

    # Here the population is filtered into 2:
    # 1. The already-evaluated list
    evaluated_pop = list()
    # 2. The pending list
    pending_pop = list()

    # DO for all in population
    while unique_pop:
        indiv = unique_pop.pop()

        # First, go into the results table and select this individual
        qry = results_table.select(results_table.c.hash ==  indiv.__hash__())
        res = engine.execute(qry).fetchall()


        if not res:
            # This is a new individual, needs evaluation
            pending_pop.append(indiv)

        else:
            # This individual has already been evaluated
            # This should return exactly one row
            assert(len(res) == 1)
            row = res[0]

            # Select and assign the fitness rows for this individual
            objectives = [row[col] for col in objective_columns]
            indiv.fitness = zip(objective_names,objectives)

            evaluated_pop.append(indiv)

    logging.info("Of these {} unique individuals, {} are new, {} are existing".format(len(pending_pop)+len(evaluated_pop), len(pending_pop),len(evaluated_pop)))

    # Run all the pending individuals, append onto evaluated_pop
    for indiv in pending_pop:
        indiv = indiv.evaluate()
        evaluated_pop.append(indiv)

    # Now re-expand the population including clones
    final_pop = list()
    for indiv in population:
        # This individual MUST have been evaluated now, either newly or existing
        assert(indiv in evaluated_pop)

        # Get this individual from the evaluated set
        index = evaluated_pop.index(indiv)
        final_pop.append(evaluated_pop[index])

    # Return this generation back for addition into DB
    # add_population_db also checks first for duplicates before adding them to results
    # The generation number will be automatically added based on last gen number
    return final_pop


  
class Individual(object):
    
    """
    Holds a variable vector with labels;
    chromosome
    labels
    indices


    fitness



    The logic of the variable is stored in the design space basis vectors
    """

    def __init__(self, labels, chromosome, indices, evaluator, fitness = None):
        raise
        self.labels = labels
        self.chromosome = chromosome
        self.indices = indices
        self.evaluator = evaluator
        self.fitness = fitness

    @property
    def evaluated(self):
        if not self.fitness: return False
        else: return True

    def __str__(self):

        name_val_tuple = zip(self.labels, self.chromosome)

        these_pairs = ["{} = {}".format(*this_pair) for this_pair in name_val_tuple]
        thisStr = ", ".join(these_pairs)

        if self.fitness:
            thisStr = thisStr + " -> " + ", ".join(["{}={}".format(fit[0],fit[1]) for fit in self.fitness])
        else:
            thisStr = thisStr + " -> (Unitialized)"
        return thisStr

    # This defines the uniqueness of the individual
    def __eq__(self, other):
        if self.__hash__() == other.__hash__():
            return True
        else:
            return False

    def __hash__(self):
        """This defines the uniqueness of the individual
        The ID of an individual could be, for example, the string composed of the variable vectors
        But this would be expensive and complicated to store in a database
        The hash compresses this information to an integer value which should have no collisions
        """

        return hash(tuple(zip(self.labels,self.chromosome)))

    def __getitem__(self,index):
        return self.chromosome[index]

    def __setitem__(self,index, value):
        raise
        self.chromosome[index],

    def next(self):
        """
        Iterator over tuple of chromosomes
        """
        if self.iterIndex < len(self.chromosome):
            # This is 0 at start
            value = self.chromosome[self.iterIndex]
            self.iterIndex += 1
            return value
        else:
            raise StopIteration

    def __iter__(self):
        # Start iteration at 0
        self.iterIndex = 0
        return self

    def clone(self):
        raise
        clonedIndiv = Individual(self.chromosome)
        return clonedIndiv

    def evaluate(self):
        return self.evaluator(self)'''
Created on 28.07.2014

@author: jon
'''
