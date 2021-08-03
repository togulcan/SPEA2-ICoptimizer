class Fitness:

    __slots__ = ("total_error", "strength", "rawfitness",
                 "distance", "fitness")

    def __init__(self, N: int):
        self.total_error = 0.0
        self.strength = 0
        self.rawfitness = 0
        self.distance = [0.0] * N
        self.fitness = 0.0

    def __repr__(self) -> str:
        return f"Fitness(error:{self.total_error}, rawfitness:{self.rawfitness})"
