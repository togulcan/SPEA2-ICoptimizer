import copy
import pickle
import itertools as it
import numpy as np
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

    def __init__(self, saving_format='instance',
                 only_cct=False, circuit_config=None,
                 spea2_config=None):
        self.saving_format = saving_format
        self.only_cct = only_cct
        self.saved_file_path = None
        self.circuit_config = circuit_config

        m = spea2_config["maximum_generation"]
        n = spea2_config["N"]
        l = len(circuit_config["topology"])

        if saving_format == 'numpy':
            self.parameters = np.zeros((m, n, l), dtype=float)
            self.arch_parameters = np.zeros((m, n, l), dtype=float)
            for k in circuit_config["output"]:
                setattr(self, k, np.zeros((spea2_config["maximum_generation"],
                                           spea2_config["N"]),
                                          dtype=float))
                setattr(self, "arch_" + k, np.zeros((spea2_config["maximum_generation"],
                                                     spea2_config["N"]),
                                                    dtype=float))
        else:
            self.pool = []

    def append(self, generation):
        if self.saving_format == 'instance':
            self._append_as_instance(generation)
        elif self.saving_format == 'numpy':
            self._append_as_nparray(generation)
        else:
            raise ValueError(f"Could not recognized {self.saving_format}")

    def save(self, saving_path, cct_name, kii):
        today = datetime.now()
        file_name = today.strftime(cct_name + " d-%Y.%m.%d h-%H.%M ")
        file_name += 'gen-0to' + str(kii)
        with open(saving_path + file_name, 'wb') as f:
            pickle.dump(self, f)
        self.saved_file_path = saving_path + file_name

    @classmethod
    def load(cls, loading_path):
        with open(loading_path, 'rb') as f:
            return pickle.load(f)

    def _append_as_instance(self, generation):
        generation_ = copy.deepcopy(generation)
        if self.only_cct:
            generation_.individuals = [copy.deepcopy(ind).circuit
                                       for ind in generation.individuals]
            generation_.archive_inds = [copy.deepcopy(ind).circuit
                                        for ind in generation.individuals]
        self.pool.append(generation_)

    def _append_as_nparray(self, generation):
        for attr in self.__dict__:
            attr_obj = getattr(self, attr)
            if isinstance(attr_obj, np.ndarray):
                if attr.startswith('arch_'):
                    attr_obj[generation.kii] = [getattr(ind.circuit, attr.replace('arch_',''))
                                                for ind in generation.archive_inds]
                else:
                    attr_obj[generation.kii] = [getattr(ind.circuit, attr)
                                                for ind in generation.individuals]
