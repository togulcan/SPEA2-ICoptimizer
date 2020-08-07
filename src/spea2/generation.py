import os
import pickle
import itertools
import numpy as np
import itertools as it
from typing import List
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, wait

from config import configs
from .individual import Individual
from .helperfuncs import chunk
from ..src import (
    Circuit, CircuitCreator, SimulationFailedError
)


class Generation:

    PROPERTIES = configs.get("CIRCUIT")

    def __init__(self, N: int = None, kii: int = None):
        self.N = N
        self.kii = kii
        self.individuals: List[Individual] = []
        self.archive_inds: List[Individual] = []

    def population_initialize(self, initializer_type: str):
        for _ in range(self.N):
            circuit = CircuitCreator.create(self.PROPERTIES['TYPE'], initializer_type)
            new_individual = Individual(circuit, self.N)
            self.individuals.append(new_individual)

    @classmethod
    def new_generation_from_parameters(cls, 
            parameters: List[list], N, kii) -> List[Individual]:

        gen = Generation(N=N, kii=kii)

        for params in parameters:
            circuit = CircuitCreator.create(
                    cls.PROPERTIES['TYPE'],
                    initializer_type='Normal', params=params)
            new_individual = Individual(circuit, N)
            gen.individuals.append(new_individual)

        return gen

    def simulate(self, path, multithread=1, algorithm=None):
        """ Simulate each individual inside the generation """

        if multithread == 0:
            for ind in self.individuals:
                while ind.status != 'simulated':
                    try:
                        ind.circuit.simulate(path)
                    except SimulationFailedError:
                        if algorithm is not None:
                            ind = algorithm.produce_new_individual()
                        else:
                            circuit = CircuitCreator.create(
                                self.PROPERTIES['TYPE'],
                                initializer_type='Random')
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
                            self.PROPERTIES['TYPE'],
                            initializer_type='Random')
                        inds[n] = Individual(circuit, self.N)
            else: return

class GenerationPool:
    
    def __init__(self, save_format=None):
        self.save_format = save_format

    def append(self, generation):
        pass
