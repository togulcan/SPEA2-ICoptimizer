import math
from typing import List


def get_normalize_constants(inds, archive_inds = None):

    """
    In order to normalize targets between 0-1 we need to find
    the maximum values of the targets.

    Args:
        inds (List[Individual]): all individual objects the 
        generation contains in its new pool.
        
        archive_inds (List[Individual]): all individual objects the 
        generation contains in its archive pool.
        
    Returns:
        List[float]: Maximum target values in individuals and
        archive individuals combined. If archive individuals
        are not present (only in the first generation)
        it only returns the maximum value of individuals.
    """
    # Avoid mutable default value
    archive_inds = [] if archive_inds is None else archive_inds

    return [max(ind.targets[j] for ind in inds + archive_inds)
            for j in range(len(inds[0].TARGETS))]


def calculate_distance(first_ind, second_ind,
                       normalize_values: List[float]) -> float:
    """ Calculate the euclidian distance between two individuals."""
    dist = 0.0
    for i, tars in enumerate(zip(
            first_ind.targets, second_ind.targets)):
        dist += ((tars[0] - tars[1]) / normalize_values[i]) ** 2
    dist = math.sqrt(dist)
    return dist


def compare_targets(first_ind, second_ind) -> bool:
    """
    Compare all targets of the individuals and return if targets of first_ind
    satisfy the conditions. i.e if all targets of the first_ind are superior than
    the targets of the second_ind it returns True
    """
    for tars in zip(first_ind.targets, second_ind.targets):
        if not tars[0] > tars[1]:
            return False
    return True


def calculate_fitness_value(fitness,
                            normalize_rawfitness: int,
                            kii: int) -> float:
    """ Calculates and returns final fitness values of each individuals"""
    if normalize_rawfitness != 0:
        fit = fitness.rawfitness / normalize_rawfitness \
            + fitness.total_error * (20 + kii ** 4) * 1e-8\
            + 0.1 / (fitness.distance + 2)
    else:
        fit = fitness.total_error * (20 + kii ** 4) * 1e-8 \
            + 0.1 / (fitness.distance + 2)
    return fit


def calculate_total_error(ind) -> float:
    """
    Calculate total error which occurs when the involved values
    of the individuals exceeds constraint limits.
    """
    total_error = 0.0
    for i in range(len(ind.CONSTRAINTS)):
        if ind.constraint_operations[i] == 'max':
            if ind.constraint_values[i] > ind.constraint_constants[i]:
                total_error += abs(
                    ind.constraint_values[i] - ind.constraint_constants[i]
                ) / ind.constraint_constants[i]
        elif ind.constraint_operations[i] == 'min':
            if ind.constraint_values[i] < ind.constraint_constants[i]:
                total_error += abs(
                    ind.constraint_values[i] - ind.constraint_constants[i]
                ) / ind.constraint_constants[i]
    return total_error
