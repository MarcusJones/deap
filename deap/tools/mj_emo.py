from collections import defaultdict
from itertools import chain
from operator import attrgetter, itemgetter
import random
__all__ = ['mj_selTournamentDCD', 'mj_selTournamentDCD','mj_selNSGA2',]

def mj_selNSGA2(individuals, k, nd='standard'):
    """Modified MJ
    First perform ND Sort to sort individuals into fronts
    For each front, assign a crowding distance
    Finally choose the best and return
    Only operates on OSpace! Can
    """
    
    """Apply NSGA-II selection operator on the *individuals*. Usually, the
    size of *individuals* will be larger than *k* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *k* will have no effect other
    than sorting the population according to their front rank. The
    list returned contains references to the input *individuals*. For more
    details on the NSGA-II operator see [Deb2002]_.
    
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param nd: Specify the non-dominated algorithm to use: 'standard' or 'log'.
    :returns: A list of selected individuals.
    
    .. [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
       non-dominated sorting genetic algorithm for multi-objective
       optimization: NSGA-II", 2002.
    """
    
    #===========================================================================
    # Sort into fronts, only operates in OSpace
    #===========================================================================
    if nd == 'standard':
        pareto_fronts = mj_sortNondominated(individuals, k)
    elif nd == 'log':
        pareto_fronts = mj_sortLogNondominated(individuals, k)
    else:
        raise Exception('selNSGA2: The choice of non-dominated sorting '
                        'method "{0}" is invalid.'.format(nd))
        
    #===========================================================================
    # Assign crowding distance to fitness attribute, only in OSpace
    #===========================================================================
    for front in pareto_fronts:
        mj_assignCrowdingDist(front)
    
    
    # Just flatten the fronts
    #i.e. chain('ABC', 'DEF') --> A B C D E F
    chosen = list(chain(*pareto_fronts[:-1]))
    # The last front is not part of chosen?
    
    
    k = k - len(chosen)
    # Check here something?
    if k > 0:
        sorted_front = sorted(pareto_fronts[-1], key=attrgetter("Fitness.crowding_dist"), reverse=True)
        chosen.extend(sorted_front[:k])
    return chosen


def mj_sortNondominated(individuals, k, first_front_only=False):
    """Modified MJ
    Sort into fronts
    Only operates in objective space, unchanged from original!
    """
    
    
    """Sort the first *k* *individuals* into different nondomination levels 
    using the "Fast Nondominated Sorting Approach" proposed by Deb et al.,
    see [Deb2002]_. This algorithm has a time complexity of :math:`O(MN^2)`, 
    where :math:`M` is the number of objectives and :math:`N` the number of 
    individuals.
    
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :param first_front_only: If :obj:`True` sort only the first front and
                             exit.
    :returns: A list of Pareto fronts (lists), the first list includes 
              nondominated individuals.

    .. [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
       non-dominated sorting genetic algorithm for multi-objective
       optimization: NSGA-II", 2002.
    """
    


    if k == 0:
        return []
    
    # The dictionary stores a dictionary 
    # The keys are the fitness
    # The values are the individuals with this fitness
    # Therefore, there should be no more than 1 individual per fitness if the function is one to one
    map_fit_ind = defaultdict(list)
    for ind in individuals:
        map_fit_ind[ind.Fitness].append(ind)
    fits = map_fit_ind.keys()
    
    #print(map_fit_ind)
    #print(fits)
    
    current_front = []
    next_front = []
    dominating_fits = defaultdict(int)
    dominated_fits = defaultdict(list)
    
    # Rank first Pareto front
    # Loop over the fitnesses
    for i, fit_i in enumerate(fits):
        #print("Next i", i, fit_i)
        
        for fit_j in fits[i+1:]:
            #print(fit_i, fit_j)
            #print(fit_i.dominates(fit_j), fit_j.dominates(fit_i))
            if fit_i.dominates(fit_j):
                dominating_fits[fit_j] += 1
                dominated_fits[fit_i].append(fit_j)
            elif fit_j.dominates(fit_i):
                dominating_fits[fit_i] += 1
                dominated_fits[fit_j].append(fit_i)
        #print(dominating_fits)
        #print(dominated_fits)
        if dominating_fits[fit_i] == 0:
            current_front.append(fit_i)
    
    fronts = [[]]
    for fit in current_front:
        fronts[-1].extend(map_fit_ind[fit])
    pareto_sorted = len(fronts[-1])

    # Rank the next front until all individuals are sorted or 
    # the given number of individual are sorted.
    if not first_front_only:
        N = min(len(individuals), k)
        while pareto_sorted < N:
            fronts.append([])
            for fit_p in current_front:
                for fit_d in dominated_fits[fit_p]:
                    dominating_fits[fit_d] -= 1
                    if dominating_fits[fit_d] == 0:
                        next_front.append(fit_d)
                        pareto_sorted += len(map_fit_ind[fit_d])
                        fronts[-1].extend(map_fit_ind[fit_d])
            current_front = next_front
            next_front = []
            
    for i, fr in enumerate(fronts):
        print(i, [ind.Fitness for ind in fr])
    #print([ind.hash for ind in fronts])
    #raise Exception
    return fronts



def mj_str_assignCrowdingDist(individuals):
    """Modified MJ
    Only operates in objective space, unchanged from original!
    """
    """Assign a crowding distance to each individual's Fitness. The 
    crowding distance can be retrieve via the :attr:`crowding_dist` 
    attribute of each individual's Fitness.
    """
    if len(individuals) == 0:
        return
    
    distances = [0.0] * len(individuals)
#     print(individuals[0].Fitness.valid)
#     this_vals = individuals[0].Fitness.wvalues
#     this_weights = individuals[0].Fitness.weights
#     print(this_vals, this_weights)
#     for val, w in zip(this_vals,this_weights):
#         print(val, w)
#         print(truediv(val,w))
    #this_map = map(truediv, this_vals, this_weights)
    #print(individuals[0].Fitness.weights)
    #print([(ind.Fitness.values, i) for i, ind in enumerate(individuals)])
    #print(tuple(map(truediv, self.wvalues, self.weights)))
    crowd = [(ind.Fitness.values, i) for i, ind in enumerate(individuals)]
    #raise Exception
    nobj = len(individuals[0].Fitness.values)
    
    for i in xrange(nobj):
        crowd.sort(key=lambda element: element[0][i])
        distances[crowd[0][1]] = float("inf")
        distances[crowd[-1][1]] = float("inf")
        if crowd[-1][0][i] == crowd[0][0][i]:
            continue
        norm = nobj * float(crowd[-1][0][i] - crowd[0][0][i])
        for prev, cur, next in zip(crowd[:-2], crowd[1:-1], crowd[2:]):
            distances[cur[1]] += (next[0][i] - prev[0][i]) / norm

    for i, dist in enumerate(distances):
        individuals[i].Fitness.crowding_dist = dist



def mj_selTournamentDCD(individuals, k):
    """Tournament selection based on dominance (D) between two individuals, if
    the two individuals do not interdominate the selection is made
    based on crowding distance (CD). The *individuals* sequence length has to
    be a multiple of 4. Starting from the beginning of the selected
    individuals, two consecutive individuals will be different (assuming all
    individuals in the input list are unique). Each individual from the input
    list won't be selected more than twice.
    
    This selection requires the individuals to have a :attr:`crowding_dist`
    attribute, which can be set by the :func:`assignCrowdingDist` function.
    
    :param individuals: A list of individuals to select from.
    :param k: The number of individuals to select.
    :returns: A list of selected individuals.
    """
    
    assert len(individuals) % 4 == 0, "This selection MUST operate on population multiples of 4!"
    
    def tourn(ind1, ind2):
        if ind1.Fitness.dominates(ind2.Fitness):
            return ind1
        elif ind2.Fitness.dominates(ind1.Fitness):
            return ind2

        if ind1.Fitness.crowding_dist < ind2.Fitness.crowding_dist:
            return ind2
        elif ind1.Fitness.crowding_dist > ind2.Fitness.crowding_dist:
            return ind1

        if random.random() <= 0.5:
            return ind1
        return ind2

    # Shuffle the individuals
    individuals_1 = random.sample(individuals, len(individuals))
    individuals_2 = random.sample(individuals, len(individuals))
    
    # This assertion is always true, each list holds all the original individuals, just the order is changed
    #assert(sorted([ind.Fitness.values for ind in individuals_1]) == sorted([ind.Fitness.values for ind in individuals_2]))
    
    raise Exception
    chosen = []
    
    # Do this tournament 4 times until done
    for i in xrange(0, k, 4):
        chosen.append(tourn(individuals_1[i],   individuals_1[i+1]))
        chosen.append(tourn(individuals_1[i+2], individuals_1[i+3]))
        chosen.append(tourn(individuals_2[i],   individuals_2[i+1]))
        chosen.append(tourn(individuals_2[i+2], individuals_2[i+3]))

    return chosen



def mj_assignCrowdingDist(individuals):
    """Assign a crowding distance to each individual's Fitness. The 
    crowding distance can be retrieve via the :attr:`crowding_dist` 
    attribute of each individual's Fitness.
    """
    if len(individuals) == 0:
        return
    
    distances = [0.0] * len(individuals)
    crowd = [(ind.Fitness.values, i) for i, ind in enumerate(individuals)]
    
    # Number objectives
    nobj = len(individuals[0].Fitness.values)
    
    for i in xrange(nobj):
        crowd.sort(key=lambda element: element[0][i])
        distances[crowd[0][1]] = float("inf")
        distances[crowd[-1][1]] = float("inf")
        if crowd[-1][0][i] == crowd[0][0][i]:
            continue
        norm = nobj * float(crowd[-1][0][i] - crowd[0][0][i])
        for prev, cur, next in zip(crowd[:-2], crowd[1:-1], crowd[2:]):
            distances[cur[1]] += (next[0][i] - prev[0][i]) / norm

    for i, dist in enumerate(distances):
        individuals[i].Fitness.crowding_dist = dist
        
