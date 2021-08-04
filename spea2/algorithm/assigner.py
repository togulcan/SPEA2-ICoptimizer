from heapq import nsmallest

from .helperfuncs import (
    calculate_distance, calculate_fitness_value,
    calculate_total_error, compare_targets,
    get_normalize_constants
)


class FitnessAssigner:

    @classmethod
    def assign_fitness_first(cls, gen):
        """
        Assign fitness values for the first generation. kii=0

        Args:
            gen (generation.Generation): the first generation
        """
        normalize_constants = get_normalize_constants(gen.individuals)
        for ind1 in gen.individuals:
            for j, ind2 in enumerate(gen.individuals):

                if compare_targets(ind1, ind2):
                    ind1.fitness.strength += 1

                elif compare_targets(ind2, ind1):
                    ind1.fitness.rawfitness += 1

                ind1.fitness.distance[j] = calculate_distance(
                    ind1,
                    ind2,
                    normalize_constants
                )

            ind1.fitness.distance = nsmallest(2, ind1.fitness.distance)[-1]
            ind1.fitness.total_error = calculate_total_error(ind1)

        max_rawfitnesses = max(
            ind.fitness.rawfitness for ind in gen.individuals)

        for ind in gen.individuals:
            ind.fitness.fitness = calculate_fitness_value(
                ind.fitness,
                max_rawfitnesses,
                gen.kii
            )

    def assign_fitness(self, next_gen, gen):
        """
        Assign fitness values to the generation and archive
        generation whose kii>1.

        Args:
            next_gen (generation.Generation): the last generation
            gen (generation.Generation): the before generation
        """
        gen.reset_arch_fitness()

        self._assign_total_error(
            next_gen.individuals,
            gen.archive_inds
        )

        self._assign_strength(
            next_gen.individuals,
            gen.archive_inds
        )

        self._assign_rawfitness(
            next_gen.individuals,
            gen.archive_inds
        )

        distance_normalize = get_normalize_constants(
            next_gen.individuals,
            gen.archive_inds
        )

        distance_normalize_archive = get_normalize_constants(
            gen.archive_inds
        )

        self._assign_distance(
            next_gen.individuals,
            gen.archive_inds,
            distance_normalize,
            distance_normalize_archive
        )

        self._assign_fitness(
            next_gen.individuals,
            gen.archive_inds,
            next_gen.kii
        )

    @staticmethod
    def _assign_total_error(inds, arch_inds):
        """
        Assign errors to the individuals.
        Args:
            inds (individual.Individual):
            arch_inds (individual.Individual):
        """
        for ind, arch_ind in zip(inds, arch_inds):
            ind.fitness.total_error = calculate_total_error(ind)
            arch_ind.arch_fitness.total_error = calculate_total_error(arch_ind)

    @staticmethod
    def _assign_strength(inds, arch_inds):
        """ Assign strength values to new generation """
        for ind1, arch_ind1 in zip(inds, arch_inds):
            for ind2, arch_ind2 in zip(inds, arch_inds):

                if compare_targets(ind1, ind2) \
                        or compare_targets(ind1, arch_ind2):
                    ind1.fitness.strength += 1

                if compare_targets(arch_ind1, ind2) \
                        or compare_targets(arch_ind1, arch_ind2):
                    arch_ind1.arch_fitness.strength += 1

    @staticmethod
    def _assign_rawfitness(inds, arch_inds):
        """ Assign rawfitness values to new generation """
        for ind1, arch_ind1 in zip(inds, arch_inds):
            for ind2, arch_ind2 in zip(inds, arch_inds):

                if compare_targets(ind2, ind1):
                    ind1.fitness.rawfitness += ind2.fitness.strength

                if compare_targets(arch_ind2, ind1):
                    ind1.fitness.rawfitness += arch_ind2.arch_fitness.strength

                if compare_targets(ind2, arch_ind1):
                    arch_ind1.arch_fitness.rawfitness += ind2.fitness.strength

                if compare_targets(arch_ind2, arch_ind1):
                    arch_ind1.arch_fitness.rawfitness += arch_ind2.arch_fitness.strength

    @staticmethod
    def _assign_distance(inds, arch_inds, normalize, normalize_arc):
        """
        Assign distance values to new generation.

        Args:
            inds (individual.Individual):
            arch_inds (individual.Individual):
            normalize (List[float]): the highest values for each targets among individuals.
            normalize_arc (List[float]): the highest values for each targets among
                individuals in archive.
        """
        for ind1, arch_ind1 in zip(inds, arch_inds):
            d1 = [0.0] * len(inds)
            d2 = [0.0] * len(inds)
            for j, arch_ind2 in enumerate(arch_inds):
                d1[j] = calculate_distance(ind1, arch_ind2, normalize)
                d2[j] = calculate_distance(arch_ind1, arch_ind2, normalize_arc)
            ind1.fitness.distance = min(d1)
            arch_ind1.arch_fitness.distance = nsmallest(2, d2)[-1]

    @staticmethod
    def _assign_fitness(inds, arch_inds, kii):
        """ Assign total fitness values to individual.fitness """
        normalize_rawfitness = max([ind.fitness.rawfitness for ind in inds])
        normalize_rawfitness_arch = max(
            [ind.fitness.rawfitness for ind in arch_inds])

        for ind, arch_ind in zip(inds, arch_inds):
            ind.fitness.fitness = calculate_fitness_value(
                ind.fitness,
                normalize_rawfitness,
                kii
            )

            arch_ind.arch_fitness.fitness = calculate_fitness_value(
                arch_ind.arch_fitness,
                normalize_rawfitness_arch,
                kii
            )
