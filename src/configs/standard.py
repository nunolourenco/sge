import sys
from rng_seeds import *


POPULATION_SIZE = 1000
NUMBER_OF_ITERATIONS = 51
ELITISM = 100
TOURNAMENT = 3
PROB_CROSSOVER = 0.9
PROB_MUTATION = 0.05
RUN = len(sys.argv) > 1 and int(sys.argv[1]) or 0
SEED = seeds[RUN]
sampling_snap = [0,25, 50]
