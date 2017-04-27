import sys
import random
import copy
import json
import os
from configs.standard import *

def generate_sge_individual():
    decimal_genome = []
    genome_size = GRAMMAR.count_number_of_non_terminals()
    number_of_references_to_non_terminal = GRAMMAR.count_references_to_non_terminals()
    size_of_gene = GRAMMAR.count_number_of_options_in_production()
    for nt in GRAMMAR.get_non_terminals():
        if nt not in number_of_references_to_non_terminal:
            gene = [random.randint(0, size_of_gene[nt] - 1)]
        else:
            gene = [random.randint(0, size_of_gene[nt] - 1) for i in xrange(number_of_references_to_non_terminal[nt])]
        decimal_genome.append([gene])
    return decimal_genome

model = {
            'generate': generate_sge_individual,
            'mutate': lambda current_gene, max_gene: random.choice([i for i in xrange(max_gene)])
}

def generate_random_individual():
    genotype = model['generate']()
    return {'genotype': genotype, 'fitness': None }


def generate_initial_population():
    for i in range(POPULATION_SIZE):
        yield generate_random_individual()


def evaluate(ind, eval_func):
    mapping_values = [0 for i in ind['genotype']]
    ind['phenotype'] = GRAMMAR.mapping(ind['genotype'], mapping_values)
    quality, other_info = eval_func.evaluate(ind['phenotype'])
    ind['fitness'] = quality
    ind['other_info'] = other_info
    ind['mapping_values'] = mapping_values


def choose_indiv(population):
    pool = random.sample(population, TOURNAMENT)
    pool.sort(key=lambda i: i['fitness'])
    return copy.deepcopy(pool[0])


def crossover(p1, p2):
    xover_p_value = 0.5
    mask = [random.random() for i in xrange(GRAMMAR.count_number_of_non_terminals())]
    genotype = []
    for index, prob in enumerate(mask):
        if prob < xover_p_value:
            genotype.append(p1['genotype'][index][ : ])
        else:
            genotype.append(p2['genotype'][index][ : ])
    return {'genotype': genotype, 'fitness': None, 'mapping_values' : map(lambda x, y: max(x,y), p1['mapping_values'],p2['mapping_values'])}


def mutate(p):
    p = copy.deepcopy(p)
    p['fitness'] = None
    size_of_genes = GRAMMAR.count_number_of_options_in_production()
    mutable_genes = [index for index, nt in enumerate(GRAMMAR.get_non_terminals()) if size_of_genes[nt] != 1]
    for at_gene in mutable_genes:
        if random.random() < PROB_MUTATION:
            nt = list(GRAMMAR.get_non_terminals())[at_gene]
            temp = p['mapping_values']
            position_to_mutate = 0
            if temp[at_gene] > 1:
                position_to_mutate = random.randint(0,temp[at_gene] - 1)
            current_value = p['genotype'][at_gene][0][position_to_mutate]
            choices = filter(lambda x: x!= current_value, range(0,size_of_genes[nt]))
            if len(choices) == 0:
                choices = range(0, size_of_genes[nt])
            p['genotype'][at_gene][0][position_to_mutate] = random.choice(choices)
    return p


def prepare_dumps(experience_name):
    os.makedirs('dumps/%s/run_%d' % (experience_name, RUN))


def save(population, it, experience_name):
    to_save = []
    app = to_save.append
    for ind in population:
        cp_ind = {}
        for key, value in ind.iteritems():
            if key != 'genotype':
                cp_ind[key] = value
        app(cp_ind)
    c = json.dumps(to_save)
    open('dumps/%s/run_%d/iteration_%d.json' % (experience_name, RUN, it), 'w').write(c)


def save_progress_report(progress_report, experience_name):
    open('dumps/%s/run_%d/progress_report.csv' % (experience_name, RUN), 'w').write(progress_report)


def evolutionary_algorithm(grammar = "", exp_name = "", eval_func = ""):
    global GRAMMAR
    experience_name = exp_name
    GRAMMAR = grammar
    random.seed(SEED)
    stats = ""
    progress_report = "Generation,Best,Mean\n"
    prepare_dumps(experience_name)
    if len(sys.argv) > 2:
        population = json.load(open(sys.argv[2]))
        it = int(sys.argv[2].split(".")[0].split("_")[-1])
    else:
        population = list(generate_initial_population())
        it = 0
    for it in range(it, NUMBER_OF_ITERATIONS):
        for i in population:
            if i['fitness'] == None:
                evaluate(i, eval_func)
        population.sort(key = lambda x: x['fitness'])
        best = population[0]
        if 'test_error' in best['other_info']:
            stats = "" + str(it) + "," + str(best['fitness']) + "," + str((float(sum([ind['fitness'] for ind in population])) / float(POPULATION_SIZE))) + "," + str(best['other_info']['test_error'])
        else:
            stats = "" + str(it) + "," + str(best['fitness']) + "," + str((float(sum([ind['fitness'] for ind in population])) / float(POPULATION_SIZE)))
        print stats#, best['phenotype']
        progress_report += stats + "\n"

        if it in sampling_snap:
            save(population, it, experience_name)
        new_population = population[:ELITISM]

        while len(new_population) < POPULATION_SIZE:
            if random.random() < PROB_CROSSOVER:
                p1 = choose_indiv(population)
                p2 = choose_indiv(population)
                ni = crossover(p1, p2)
            else:
                ni = choose_indiv(population)
            ni = mutate(ni)
            new_population.append(ni)
        population = new_population
    save_progress_report(progress_report, experience_name)
