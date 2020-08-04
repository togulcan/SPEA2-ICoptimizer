from math import ceil
import numpy as np
from random import randrange, uniform

from .generation import Generation
from .individual import Individual


def _single_mating(gen: Generation) -> Individual:
    """ Choose a parent from archive randomly """
    p1 = ceil(randrange(gen.N))
    p2 = ceil(randrange(gen.N))

    while p1 == p2:
        p2 = ceil(randrange(gen.N))

    parent1 = gen.archive_inds[p1]
    parent2 = gen.archive_inds[p2]

    if hasattr(parent1, 'coming_from') and hasattr(parent2, 'coming_from'):
        if parent1.coming_from == 'last_gen':
            fitness1 = parent1.fitness.fitness
        elif parent1.coming_from == 'last_arch':
            fitness1 = parent1.arch_fitness.fitness
        
        if parent2.coming_from == 'last_gen':
            fitness2 = parent2.fitness.fitness
        elif parent2.coming_from == 'last_arch':
            fitness2 = parent2.arch_fitness.fitness

        raise ValueError(f"Can not recognized ind.coming_from")
    else:
        fitness1 = parent1.fitness.fitness
        fitness2 = parent2.fitness.fitness

    if fitness1 > fitness2:
        return parent2
    else:
        return parent1


def _single_mutation(ind: Individual,
                    upper_bound, lower_bound) -> Individual:

    mutation_step_size = 0.1 + 0.2 * uniform(0, 1)
    mutation = True if uniform(0, 1) > mutation_step_size else False
    
    if mutation:
        param_index_to_be_mutated = randrange(0, len(ind.circuit.parameters))
        difference_bound = np.subtract(upper_bound[param_index_to_be_mutated],
                                    lower_bound[param_index_to_be_mutated])
        multiplied_difference_bound = np.multiply(difference_bound, uniform(0, 1))
        
        ind.circuit.parameters[param_index_to_be_mutated] = np.add(
            lower_bound[param_index_to_be_mutated], multiplied_difference_bound)
    return ind


class EvolutionaryAlgorithm:
    """ SPEA2 evolutionary algorithm class. """

    def __init__(self, generation: Generation, 
                    next_generation: Generation = None):
        self.gen = generation
        self.next_gen = next_generation
        self.N = generation.N
    
    def mating_pool(self) -> Individual:
        """
        Randomly selects two parent from archive and yield 
        the one which has lower fitness value i.e. well performance.
        """
        seen = set()
        while True:
            selected_parent = _single_mating(self.next_gen)
            if id(selected_parent) not in seen:
                seen.add(id(selected_parent))
                yield selected_parent
            if len(seen) == len(self.next_gen.archive_inds):
                seen = set()

    def cross_mutation_pool(self):
        """ Apply mutation to randomly selected children"""

        recombination_coefficient = 0.8

        while True:
            parent1, parent2 = (yield)

            circuit1 = parent1.circuit * recombination_coefficient +\
                            parent2 * (1 - recombination_coefficient)
            child1 = Individual(circuit1, self.N)

            circuit2 = parent2.circuit * recombination_coefficient +\
                            parent1 * (1 - recombination_coefficient)
            child2 = Individual(circuit2, self.N)
            
            mutated_child1 = _single_mutation(child1, 
                    circuit1.PROPERTIES['upper_bound'], circuit1.PROPERTIES['lower_bound'])
            mutated_child2 = _single_mutation(child2, 
                    circuit2.PROPERTIES['upper_bound'], circuit2.PROPERTIES['lower_bound'])

            yield mutated_child1, mutated_child2

    def select_archive(self):
        
        archive_inds_temp = set()
        for ind, arch_ind in zip(self.next_gen.individuals, self.gen.archive_inds):
           
            if ind.fitness.fitness == 0 and ind.fitness.total_error == 0:
                if ind not in archive_inds_temp:
                    archive_inds_temp.add(ind)
                    ind.coming_from = 'last_gen'

            if arch_ind.arch_fitness.fitness == 0 and \
                    arch_ind.arch_fitness.total_error == 0:
                if arch_ind not in archive_inds_temp:
                    archive_inds_temp.add(arch_ind)
                    arch_ind.coming_from = 'last_arch'

        all_fitness_temp = [ind.fitness.fitness for ind in self.next_gen.individuals] + \
                           [ind.fitness.fitness for ind in self.gen.archive_inds]
        indexes = sorted(range(len(all_fitness_temp)),
                         key=lambda k: all_fitness_temp[k])

        if len(archive_inds_temp) < self.next_gen.N:
            i = 0
            while len(archive_inds_temp) < self.next_gen.N:
                if indexes[i] < self.next_gen.N:
                    if self.next_gen.individuals[indexes[i]] not in archive_inds_temp:
                        ind_to_append = self.next_gen.individuals[indexes[i]]
                        archive_inds_temp.add(ind_to_append)
                        ind_to_append.coming_from = 'last_gen'
                else:
                    if self.gen.archive_inds[indexes[i] - self.gen.N] not in archive_inds_temp:
                        ind_to_append = self.gen.archive_inds[indexes[i] - self.gen.N]
                        archive_inds_temp.add(ind_to_append)
                        ind_to_append.coming_from = 'last_arch'
                i += 1

        elif len(archive_inds_temp) > self.gen.N:
            while len(archive_inds_temp) > self.gen.N:
                archive_inds_temp.pop()

        return archive_inds_temp

    def produce_new_individual(self) -> Individual:
        pool = self.mating_pool()
        cross_mut = self.cross_mutation_pool()
        next(cross_mut)
        while True:
            try:
                parent1 = next(pool)
                parent2 = next(pool)
            except StopIteration:
                cross_mut.close()
                raise RuntimeError(f"There is no individual in archive to be yielded."
                                    f"All of them have been yielded before.")
            else:
                child1, child2 = cross_mut.send(parent1, parent2)
                yield child1, child2

    def produce(self) -> Generation:
        new_generation = Generation(self.N, self.next_gen.kii+1)
        new_ind_it = self.produce_new_individual()
        
        for _ in range(self.N):
            ind = next(new_ind_it)
            new_generation.individuals.append(ind)
        
        return new_generation

