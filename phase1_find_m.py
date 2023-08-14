# Phase 1 for computing m, the largest step number
# for failure propagation

from z3 import *  # Please install z3py with "pip install z3py"
import re
import itertools

# Pls hard-code the input file name here
file = "case300IIRsAtTimeStep1.txt"

# Read input file
inputtext = []
with open(file) as fileobj:
    for line in fileobj:
        inputtext.append(line)

# elements (ie. entities)
ELEMENTS = set()
for line in inputtext:
    ELEMENTS = ELEMENTS | set(line.split())
ELEMENTS.remove('<-')
ELEMENTS = list(ELEMENTS)

NUM_ELEMENTS = len(ELEMENTS)
BOUND = NUM_ELEMENTS + 1

print("input # initial failures (K) <=", NUM_ELEMENTS)
INPUTNUMBER = int(input())

# interpret relations
# ex. [('G2', [['T1', 'G1'], ['T4', 'G3'], ['G2']]), ...
relations = []
for line in inputtext:
    entity, expr = line.split("<-")
    entity = entity.strip()
    expr = re.split('  +', expr)
    single_relation = []
    for term in expr:
        entities = term.split()
        single_relation.append(entities)
    relations.append((entity, single_relation))

# Find elements that have no relation
independent_entries = set(ELEMENTS)
for entity, single_relation in relations:
    independent_entries.remove(entity)
independent_entries = list(independent_entries)

s = Solver()
# q=Optimize()

# STEP 0
variables = {}
step = 0
for elem in ELEMENTS:
    variable_key = (elem, step)
    variables[variable_key] = Bool(str(variable_key))

# print(NUM_ELEMENTS - INPUTNUMBER)
initial_states = [variables[elem, 0] for elem in ELEMENTS]
initial_failures = AtLeast(*initial_states, NUM_ELEMENTS - INPUTNUMBER)
s.add(initial_failures)
initial_failures = AtMost(*initial_states, NUM_ELEMENTS - INPUTNUMBER)
s.add(initial_failures)

# STEP >0
for step in range(1, BOUND+1):
    for elem in ELEMENTS:
        variable_key = (elem, step)
        variables[variable_key] = Bool(str(variable_key))

    for entity in independent_entries:
        s.add(variables[entity, step - 1] == variables[entity, step])
# relation
    for entity, terms in relations:
        constraint = []
        for term in terms:
            term_step = list(itertools.product(term, [step - 1]))
            product = [variables[key] for key in term_step]
            constraint.append(And(product))
        or_constraint = Or(constraint)
        and_constraint = And(or_constraint, variables[entity, step-1])
        s.add(variables[entity, step] == and_constraint)
        # print(terms_step)

    # stopped?
    constraint = []
    for elem in ELEMENTS:
        constraint.append(And(variables[elem, step - 1],
                              Not(variables[elem, step])))
    or_constraint = Or(constraint)
    s.add(or_constraint)

    if s.check() == sat:
        model_obtained = s.model()
    else:
        break

# print(s.model())
# print(s)
if 'model_obtained' in locals():
    print(model_obtained)
print("max", step - 1)
step_number = step - 1
exit(0)

# [Phase 2 using SAT]
#
# The rest is only for experimental use.
# This solves Phase 2 by repeating SAT solving
# with the number of induced failures being varied.
# To use this, comment out the above exit(0) statement.

q = Solver()

initial_states = [variables[elem, 0] for elem in ELEMENTS]
initial_failures = AtLeast(*initial_states, NUM_ELEMENTS - INPUTNUMBER)
q.add(initial_failures)
initial_failures = AtMost(*initial_states, NUM_ELEMENTS - INPUTNUMBER)
q.add(initial_failures)

# STEP >0
for step in range(1, step_number+1):
    for entity in independent_entries:
        q.add(variables[entity, step - 1] == variables[entity, step])
# relation
    for entity, terms in relations:
        constraint = []
        for term in terms:
            term_step = list(itertools.product(term, [step - 1]))
            product = [variables[key] for key in term_step]
            constraint.append(And(product))
        or_constraint = Or(constraint)
        and_constraint = And(or_constraint, variables[entity, step-1])
        q.add(variables[entity, step] == and_constraint)
        # print(terms_step)
broken_number = INPUTNUMBER + step_number
broken_number_keep = broken_number
while(NUM_ELEMENTS > broken_number):
    print(NUM_ELEMENTS - broken_number)
    final_states = [variables[elem, step_number] for elem in ELEMENTS]
    final_failures = AtMost(*final_states, NUM_ELEMENTS - broken_number)
    q.add(final_failures)
    broken_number_keep = broken_number

    if q.check() == sat:
        model_obtained = q.model()
        count = 0
        for elem in ELEMENTS:
            variable_key = (elem, step_number)
            variables[variable_key] = Bool(str(variable_key))
            if model_obtained[variables[variable_key]] is False:
                count = count + 1
        print('count =' + str(count))
        broken_number_keep = broken_number
        broken_number = max(broken_number + 1, count)
    else:
        print('unsat')
        break

print('max break number =' + str(broken_number_keep))
print('step0 break NODE')
for elem in ELEMENTS:
    variable_key = (elem, 0)
    variables[variable_key] = Bool(str(variable_key))
    print(str(elem) + ' =' + str(model_obtained[variables[variable_key]]))
