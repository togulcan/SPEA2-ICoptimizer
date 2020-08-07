import time
import logging
from datetime import datetime
from loguru import logger
# from matplotlib import pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D

from src import FileHandler
from src.spea2 import Generation, FitnessAssigner, EvolutionaryAlgorithm


# Set logger configurations.
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename='logs.log',
                    format=LOG_FORMAT)
logger = logging.getLogger()

# start time_perf counter.
start = time.perf_counter()

# Current generation
kii = 0

# Number of individual each generation contains
N = configs['SPEA2']['N']

# Maximum generation number
MAXIMUM_GEN = configs['SPEA2']['MAXIMUM_GEN']

# How many multithreads the process will be used
MULTITHREAD = configs['MULTITHREAD']

# Create temp file to perform simulations
file_handler = FileHandler(configs['CIRCUIT']['PATH_TO_CIRCUIT'])
file_handler.check_required_files(MULTITHREAD)
path = file_handler.get_simulation_folder()

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
# generation_pool = GenerationPool(saving_format='numpy')
# generation_pool.append(generation)

# Initialize the first generation. Either with Randomly,
# or using Low-discrepancy sequence.
generation.population_initialize('Random')

# Simulate the individuals of the generation
generation.simulate(path=path, multithread=MULTITHREAD)

# Assign fitness instance to the each individual in the generation
FitnessAssigner.assign_fitness_first(generation)

# Since it is the first generation, archive individuals and individiuals
# will be the same.
generation.archive_inds = generation.individuals

# With the help of the assigned fitness values, the algorithm
# can now produce the next generation.
next_generation = EvolutionaryAlgorithm.produce(generation)

while kii < MAXIMUM_GEN - 1:

    # Increase the current generation number
    kii += 1
    print("# Gen: ", kii)

    # Now simulate the new generation in order to calculate
    # performance values of the each circuit generation has.
    generation.simulate(path=path, multithread=MULTITHREAD)

    # Assign fitness instance to the new generation and arch_fitness
    # instance to the generation before.
    FitnessAssigner().assign_fitness(next_generation, generation)

    # Choose archive individuals based on the assigned fitness values
    algorithm = EvolutionaryAlgorithm(next_generation, generation)
    next_generation.archive_inds = algorithm.select_archive()

    # Iterate to the next generation.
    new_generation = algorithm.produce()

    # Create a shallow copy of new generation and overrides generation
    generation = next_generation
    next_generation = new_generation


stop = time.perf_counter()

logger.info(f"\nTime took for the whole process: {(stop - start) / 60} min."
            f"\nMaximum generation: {MAXIMUM_GEN} with {N} individuals for each generation."
            f"\nNumber of multithreads used: {MULTITHREAD}"
            f"\nSaving Format: {generation_pool.saving_format}"
            f"\nSaved to /data/{x} file.")

# save generations in between 0-kii
generation_pool.save_as(0, kii)