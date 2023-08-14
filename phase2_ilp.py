# Phase 2 for computing K nodes
# Produce an LP file

import re
import itertools
import sys

# file = "case6wwIIRsAtTimeStep1.txt"
file = "case14IIRsAtTimeStep1.txt"
# file = "case24_ieee_rtsIIRsAtTimeStep1.txt"

outfile = file.rstrip(".txt")
outfile = outfile.lstrip("./")
outfile = f"{outfile}.lp"

# Read input file
inputtext = []
with open(file) as fileobj:
    for line in fileobj:
        inputtext.append(line)

# elements
ELEMENTS = set()
for line in inputtext:
    ELEMENTS = ELEMENTS | set(line.split())
ELEMENTS.remove('<-')
ELEMENTS = list(ELEMENTS)

NUM_ELEMENTS = len(ELEMENTS)
BOUND = NUM_ELEMENTS + 1

print("Input #initial failures K (<= n = ", NUM_ELEMENTS, ")")
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

print("Input #steps. (<= min(n - 1 = %d, n - (#independent entities) = %d)"
      % (NUM_ELEMENTS - 1, NUM_ELEMENTS - len(independent_entries)))
NUM_STEPS = int(input())

#
CONSTRAINTS = []

# STEP 0
variables = {}
vrb = {}
step = 0
for elem in ELEMENTS:
    variable_key = (elem, step)
    vrb[variable_key] = elem + "({})".format(step)

# initial failures
line = ""
for elem in ELEMENTS:
    if line == "":
        line += vrb[elem, step]
    else:
        line += " + " + vrb[elem, step]
line += " = " + str(INPUTNUMBER)
CONSTRAINTS.append(line)

# STEP >0
for step in range(1, NUM_STEPS + 1):
    for elem in ELEMENTS:
        variable_key = (elem, step)
        vrb[variable_key] = elem + "({})".format(step)

    # entity can not resurrect
    # x' >= x   x- x' <= 0
    for elem in ELEMENTS:
        line = vrb[elem, step - 1] + " - " + vrb[elem, step] + " <= 0"
        CONSTRAINTS.append(line)

    # independent elements do not change their state
    for elem in independent_entries:
        line = vrb[elem, step - 1] + " - " + vrb[elem, step] + " = 0"
        CONSTRAINTS.append(line)

    # relation
    for entity, terms in relations:
        if len(terms) == 1:
            # single minterm case: ex. a <- b c d
            # b c d - 3a' <= 0
            term_step = list(itertools.product(terms[0], [step-1]))
            for key in term_step:
                if line == "":
                    line += vrb[key]
                else:
                    line += " + " + vrb[key]
            line += " - " + str(len(terms[0])) + " " \
                    + vrb[entity, step] + " <= 0"
            CONSTRAINTS.append(line)

            # another constraint
            # a' - a - b - c  - d <= 0
            line = vrb[entity, step] + " - " + vrb[entity, step - 1]
            for key in term_step:
                line += " - " + vrb[key]
            line += " <= 0"
            CONSTRAINTS.append(line)
        else:
            # multiple minterms case: ex. a<- bcd + ef + g
            tmp_vrb = []
            for ind, term in enumerate(terms):
                if len(term) == 1:  # ex. g
                    tmp_vrb.append(vrb[term[0], step - 1])
                else:  # bcd
                    tmp_var_name = "t_{}_{}_{}".format(entity, ind, step-1)
                    tmp_vrb.append(tmp_var_name)
                    vrb[entity, ind, step - 1] = tmp_var_name
                    # b+c+d - 3t <= 0
                    line = ""
                    term_step = list(itertools.product(term, [step - 1]))
                    for key in term_step:
                        if line == "":
                            line += vrb[key]
                        else:
                            line += " + " + vrb[key]
                    line += " - " + str(len(term)) + tmp_vrb[ind] + " <= 0"
                    CONSTRAINTS.append(line)
                    # t - b - c- d <= 0
                    line = tmp_vrb[ind]
                    for key in term_step:
                        line += " - " + vrb[key]
                    line += " <= 0"
                    CONSTRAINTS.append(line)

            # t1 + t2 + t3 - a' <= 2
            line = ""
            for tmp in tmp_vrb:
                if line == "":
                    line += tmp
                else:
                    line += " + " + tmp
            line += " - " + vrb[entity, step] + " <= " + str(len(terms) - 1)
            CONSTRAINTS.append(line)

            # 3t' - 3t -c1 -c2 -c3 <= 0
            line = str(len(terms)) + " " + vrb[entity, step]
            line += " - " + str(len(terms)) + " " + vrb[entity, step - 1]
            for tmp in tmp_vrb:
                line += " - " + tmp
            line += " <= 0"
            CONSTRAINTS.append(line)

# for LP
with open(outfile, 'w') as f:
    # [START objective]
    print("maximize", file=f)
    line = ""
    for elem in ELEMENTS:
        if line == "":
            line = line + vrb[elem, step]
        else:
            line = line + " + " + vrb[elem, step]
    print(line, file=f)
    # [END objective]

    print("subject to", file=f)
    for line in CONSTRAINTS:
        print(line, file=f)

    print("binary", file=f)
    for term in vrb:
        print(vrb[term], file=f)
