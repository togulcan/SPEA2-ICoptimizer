import copy
import pickle
import itertools as it
from typing import List
from threading import Lock
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait

from .. import CircuitCreator, SimulationFailedError
from .individual import Individual


class Generation:
    PROPERTIES = None

    def __init__(self, N: int = None, kii: int = None):
        self.N = N
        self.kii = kii
        self.individuals: List[Individual] = []
        self.archive_inds: List[Individual] = []

    def population_initialize(self, initializer_type: str):
        for _ in range(self.N):
            circuit = CircuitCreator.create(
                circuit_type=self.PROPERTIES['type'],
                initializer_type=initializer_type
            )
            new_individual = Individual(circuit, self.N)
            self.individuals.append(new_individual)

    @classmethod
    def new_generation_from_parameters(cls,
                                       parameters, N, kii):
        gen = Generation(N=N, kii=kii)
        for params in parameters:
            circuit = CircuitCreator.create(
                circuit_type=cls.PROPERTIES['type'],
                initializer_type='Normal',
                params=params
            )
            new_individual = Individual(circuit, N)
            gen.individuals.append(new_individual)
        return gen

    def simulate(self, path, multithread=1, algorithm=None):
        """ Simulate each individual inside the generation """
        if multithread == 1:
            for ind in self.individuals:
                while ind.status != 'simulated':
                    try:
                        ind.circuit.simulate(path)
                    except SimulationFailedError:
                        if algorithm is not None:
                            ind = algorithm.produce_new_individual()
                        else:
                            circuit = CircuitCreator.create(
                                circuit_type=self.PROPERTIES['type'],
                                initializer_type='Random'
                            )
                            ind = Individual(circuit, self.N)
                    else:
                        ind.status = 'simulated'
        else:
            self._simulate_inds(path, self.individuals, multithread, algorithm)

    def _simulate_inds(self, path, inds, multithread, algorithm=None):
        path_pool = tuple(path + str(x) + '\\' for x in range(8))
        lock_pool = tuple(Lock() for _ in range(8))
        indx_to_sim = range(len(inds))
        while True:
            failed_inds = []
            futures = []
            with ThreadPoolExecutor(max_workers=multithread) as executor:
                for x, path_, lock_ in zip(
                        indx_to_sim, it.cycle(path_pool), it.cycle(lock_pool)):
                    futures.append(executor.submit(inds[x].circuit.simulate, path_, lock_))
            wait(futures)
            for n, future in zip(indx_to_sim, futures):
                if future.exception() is not None:
                    inds[n].status = 'failed'
                    failed_inds.append(n)
                else:
                    inds[n].status = 'simulated'

            if failed_inds:
                indx_to_sim = failed_inds
                if algorithm is not None:
                    for n in failed_inds:
                        inds[n] = algorithm.produce_new_individual()
                else:
                    for n in failed_inds:
                        circuit = CircuitCreator.create(
                            self.PROPERTIES['type'],
                            initializer_type='Random')
                        inds[n] = Individual(circuit, self.N)
            else:
                return


class GenerationPool:

    def __init__(self, saving_format='instance', only_cct=False):
        self.saving_format = saving_format
        self.only_cct = only_cct
        self.pool = []
        self.saved_file_path = None

    def append(self, generation):
        generation_ = copy.deepcopy(generation)
        if self.saving_format == 'instance':
            if self.only_cct:
                for ind, arc_ind in zip(generation_.individuals,
                                        generation_.archive_inds):
                    ind_keys = list(ind.__dict__.keys())
                    arc_ind_keys = list(arc_ind.__dict__.keys())
                    for key in ind_keys:
                        if key != "circuit" and hasattr(ind, key):
                            delattr(ind, key)
                    for key in arc_ind_keys:
                        if key != "circuit" and hasattr(arc_ind, key):
                            delattr(arc_ind, key)

                    # if hasattr(ind, "fitness"):
                    #     del ind.fitness
                    # if hasattr(ind, "arch_fitness"):
                    #     del ind.arch_fitness
                    # if hasattr(arc_ind, "fitness"):
                    #     del arc_ind.fitness
                    # if hasattr(arc_ind, "arch_fitness"):
                    #     del arc_ind.arch_fitness
            self.pool.append(generation_)
        elif self.saving_format == 'numpy':
            pass
        else:
            raise ValueError(f"Could not recognized {self.saving_format}")

    def save(self, saving_path, cct_name, kii):
        if self.saving_format == 'instance':
            self.save_as_instance(saving_path, cct_name, kii)
        elif self.saving_format == 'numpy':
            self.save_as_numpy(saving_path, cct_name, kii)

    def save_as_instance(self, path, cct_name, kii):
        today = datetime.now()
        file_name = today.strftime(cct_name + " d-%Y.%m.%d h-%H.%M ")
        file_name += 'gen-0to' + str(kii)
        with open(path + file_name, 'wb') as f:
            pickle.dump(self.pool, f)
        self.saved_file_path = path + file_name

    def save_as_numpy(self, path, cct_name, kii):
        pass
