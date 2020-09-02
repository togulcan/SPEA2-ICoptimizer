from .circuit import *
from .filehandler import FileHandler
from .simulators import HSpiceSimulator, SimulationFailedError
from .spea2 import (
    Generation, GenerationPool, FitnessAssigner,
    EvolutionaryAlgorithm, Individual
)


def process(circuit_config: dict, spea2_config: dict, path: str,
            thread=1, saving_format='instance', only_cct=False):
    """
    The whole process is going under this function. After iterating
    the generations to the maximum_generation the data will be pickled
    to the path.
    """
    # Assign configuration to class variables. Note that these are
    # runtime assignment and can not be pickled.
    circuit.Circuit.PROPERTIES = circuit_config
    Generation.PROPERTIES = circuit_config
    Individual.TARGETS = spea2_config["targets"]
    Individual.CONSTRAINTS = spea2_config["constraints"]
    Individual.constraint_operations = [x for x in Individual.CONSTRAINTS.keys()]
    THREAD = thread
    kii = 0
    N = spea2_config["N"]
    MAXIMUM_GEN = spea2_config["maximum_generation"]
    output_path = circuit_config["path_to_output"]

    # Create first generation with N individual
    generation = Generation(N, kii)

    # Each generation will be appended to the generationpool after
    # each iteration. Since each generation contains individuals,
    # each individual contains many float values, generationpool
    # instance contains thousand and even millions float values,
    # hence memory footprint is a highly critical concern. So keeping
    # data as numpy arrays in memory would be the best choice for
    # high number of generation and individuals. Otherwise,
    # set saving_format='instance'
    generation_pool = GenerationPool(saving_format, only_cct,
                                     circuit_config, spea2_config)

    # Initialize the first generation. Either with Randomly,
    # or using Low-discrepancy sequence.
    generation.population_initialize('Random')

    # Simulate the individuals of the generation
    generation.simulate(path=path, multithread=THREAD)

    # Assign fitness instance to the each individual in the generation
    FitnessAssigner.assign_fitness_first(generation)

    # Since it is the first generation, archive individuals and individiuals
    # will be the same.
    generation.archive_inds = generation.individuals

    # Append to the pool
    generation_pool.append(generation)

    # With the help of the assigned fitness values, the algorithm
    # can now produce the next generation.
    algorithm = EvolutionaryAlgorithm(generation, generation)
    next_generation = algorithm.produce()

    while kii < MAXIMUM_GEN - 1:
        # Increase the current generation number
        kii += 1
        print("# Gen: ", kii)

        # Now simulate the new generation in order to calculate
        # performance values of the each circuit generation has.
        next_generation.simulate(path=path, multithread=THREAD, algorithm=algorithm)

        # Assign fitness instance to the new generation and arch_fitness
        # instance to the generation before.
        FitnessAssigner().assign_fitness(next_generation, generation)

        # Choose archive individuals based on the assigned fitness values
        algorithm = EvolutionaryAlgorithm(generation, next_generation)
        next_generation.archive_inds = algorithm.select_archive()

        # Iterate to the next generation.
        new_generation = algorithm.produce()

        # Create a shallow copy of new generation and overrides generation
        generation = next_generation
        next_generation = new_generation

        # Append the last generation
        generation_pool.append(generation)

    # Save pool to the path_to_output
    generation_pool.save(output_path, circuit_config["name"], kii)
    return generation_pool.saved_file_path
