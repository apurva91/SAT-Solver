# -*- coding: utf-8 -*-
"""SAT Solver

Automatically generated by Colaboratory.

# SAT Solver 
## Assignment for CS508
Name: Apurva N Saraogi

Roll Number: 160101013

### Task: 
- To design a SAT solver
- Run benchmarks on it to show solver's performance

In this implementation a CDCL based SAT solver is prepared. On the first look DPLL based SAT solver looks promising as it mostly does intutive part like purification and unit propgation, it works good for random test cases, but for industrial purposes CDCL is used mainly due to these three reasons.
- The variable is chosen randomly
- Chronologically all branches are checked out
- No learning from the current partial assignment, throws it all away.

In the implementation we take care of these three things as follows, firstly for variable selection we use the below heuristics:
- **Random**: The way it is already done.
- **Ordered**: The first variable that is unassigned in the order 1,2,3... is chosen.
- **Dynamic Largest Individual Sum (DLIS)**: The literal that occurs more frequently. By doing this we will be able to resolve maximum number of clauses at once.
- **Largest Variable Sum (LVS)**: The variable that occurs more frequently is chosen. The count is computed once in the beginning and it is static, unlike DLIS does it everytime.
- **Jeroslow–Wang (JW)**: Similar to DLIS but more weight is given to a literal in shorter clause compared to a longer clause weight is given by 2^-length.

The second and this problems are handled as they are handled commonly in CDCL solvers by doing backjumps and adding clauses whenever conflict is reached. The algorithm is explained in detail in later sections.
"""

# Importing the libraries required
import os
import time
import random
import tabulate
from orderedset import OrderedSet
import operator
import timeout_decorator
import argparse

# Strategies available
strategies = ["RAN","ORD","LVS","JW","DLIS"]

# Weight to be used in branching strategies
weight = 2

# Precomputing weights for quicker access
pow_weight = [2**(-x) for x in range(0,501)]

# Timeout a testcase
test_case_timeout = 20

implications = 0
branches = 0
strategy = "RAN"

"""Preprocessing of formula is done to reduce the size of the formula, we call this as regularizing a clause, in this we do three major things:
- if p and not(p) are in the same clause, we remove the clause
- duplicate literals from a clause are removed
- it is then sorted and returned (Helps in searching, will be shown in next sections.)

Removal of duplicate clause is done once a clause is regularized by putting them in a set.
"""

# Forumula Compression

def regularizeClause(clause):
  '''
  Args:
      clause ([int]): 
  Returns:
      [int]: Regualarized clause
  '''
  # removes duplicate literals 
  unique_clause = { x: 1 for x in clause}
  for x in unique_clause:
    # checking if for p: not p exists
    if -x in unique_clause.keys():
      return frozenset([])
  # sorting and returning list
  return frozenset(clause)

def compressCNF(clauses):
  '''
  Args:
      clauses ([[int]]): 
  Returns:
      [[int]]: Compressed Forumla
  '''
  # set of clauses and final list to be returned
  set_of_clauses = set()
  for clause in clauses:
    # regularized clause
    r_clause = regularizeClause(clause)
    # If empty clause ignore it
    if len(r_clause)==0:
      continue
    # if clause not already added then add it
    set_of_clauses.add(r_clause)
  return set_of_clauses

# Function for reading file

def readFile(input_file):
  '''
  Args:
      input_file (str): Location of the input file
  Returns:
      int: Number of Variables
      [int]: clauses
  '''
  num_of_variables = 0
  clauses = []
  # Over here opening file, then parsing it and creating input
  with open(input_file) as f:
    for line in f: 
      if line[0]=='c' or line[0]=='p' or line[0]=='%' or line[0]=='0':
        if line[0]=='p':
          num_of_variables = int(line.split()[2])
        continue
      else:
        clause = [int(tok) for tok in line.split()[:-1] if abs(int(tok))>=1 and abs(int(tok))<=num_of_variables]
        if(len(clause)>0):
          clauses.append(clause)
  
  return num_of_variables,clauses

# Utility Functions

def literal_value(literal):
  '''
  Returns the variable of the literal
  Args:
      literal (int):
  Returns:
      int: Variable
  '''  
  return abs(literal)

def literal_sign(literal):
  '''
  Returns the type of literal.
  Args:
      literal (int):
  Returns:
      bool: Postive Literal -> 1 else 0
  '''
  if literal>0:
    return 1
  else:
    return 0

def evaluate_literal(literal):
  '''
  Args:
      literal int:
  Returns: 
      int: 1 if True 0 if False -1 if unassigned
  ''' 
  if assignment[literal_value(literal)] == -1:
    return -1
  elif assignment[literal_value(literal)] == literal_sign(literal):
    return 1
  else:
    return 0 


def evaluate_clause(clause):
  '''
  Args:
      clause{int}
  Returns: 
      int: 1 if satisfied, 0 if unsatisfied, -x if x unassigned variables
  ''' 
  undecided = 0
  for literal in clause:
    if evaluate_literal(literal) == 1:
      return 1
    elif evaluate_literal(literal) == -1:
      undecided += 1
  if undecided > 0:
    return -undecided
  else:
    return 0

def get_first_literal(clause):
  '''
  Args:
      clause{int}
  Returns: 
      int: First unassigned variable in the clause
  ''' 
  for literal in clause:
    # As unassigned literal is found return
    if evaluate_literal(literal) == -1:
      return literal
  return None

def assignment_over():
  '''
  Returns:
      bool: Depicts if are all variables assigned
  ''' 
  return min(assignment[1:])!=-1

def initialize_solver():
  # Initializing solver.
  global current_level, branch_variable, propogation_history, branch_record, learnings, assignment,graph, LVS_count, implications, branches
  current_level = 0 # Stores the current level at which solver is
  branch_variable = set() # The variables on which branch is created
  branch_record = {} # Tracks level wise record of branch variable
  propogation_history = {} # Tracks all the implications done at each level
  learnings = set() # Set of all the learned clauses
  assignment = [-1]*(num_of_variables+1) # Assignment 1:True,0:False,-1:Empty
  LVS_count = [] # Only used when strategy is LVS
  graph = { variable: Node(variable) for variable in range(1,num_of_variables+1)}
  # Creating nodes for the implication graph.
  # Reset benchmarking variables
  implications = 0
  branches = 0

# Basic struct for the Node for making of implication graph
class Node:
  def __init__(self,variable):
    self.variable = variable
    self.value = -1
    self.level = -1
    self.parents = []
    self.children = []
    self.clause = None

# Branching Strategy as decsribed earlier

def DLIS():
  '''
  Returns:
      int: Literal with maximum occurences.
  ''' 
  # Calculate count of each variable
  count = { y:0 for x in range(1,num_of_variables+1) if assignment[x]==-1 for y in [x,-x]}
  for clause in clauses:
    if evaluate_clause(clause) < 0:
      for literal in clause:
        if assignment[literal_value(literal)] == -1: 
          count[literal] += 1.0
  # Choose the one which has maximum count 
  return max(count.items(), key = operator.itemgetter(1))[0]

def LVS():
  '''
  Returns:
      int: Variable with maximum occurences in the initial formula.
  ''' 

  global LVS_count
  # Check if precomputed for the current problem
  if len(LVS_count)==0:
    # If not precompute it
    LVS_count = { x:0 for x in range(1,num_of_variables+1) }
    for clause in clauses:
      for literal in clause:
        LVS_count[literal_value(literal)]+=1
  # Find maximum variable such that variable is unassigned.
  max_var = 0
  max_value = -1

  for var in range(1,num_of_variables+1):
    if assignment[var]==-1 and LVS_count[var]>max_value:
      max_value = LVS_count[var]
      max_var = var

  return max_var*random.choice([1,-1])

def JW():
  '''
  Returns:
      int: Literal with maximum weight.
  ''' 
  # Similar to the above function, instead of adding one adding weight according
  # to length of clause
  count = { y:0 for x in range(1,num_of_variables+1) if assignment[x]==-1 for y in [x,-x]}
  for clause in clauses:
    if evaluate_clause(clause) < 0:
      for literal in clause:
        if assignment[literal_value(literal)] == -1: 
          count[literal] += pow_weight[min(500,len(clause))]
  return max(count.items(), key = operator.itemgetter(1))[0]


def ORD():
  '''
  Returns:
      int: First unassigned variable in order 1,2,3...
  ''' 
  # Select first unassigned variable followed by random sign.
  for x in range(1,num_of_variables+1):
    if assignment[x] == -1:
      return x*random.choice([1,-1])


def RAN():
  '''
  Returns:
      int: Randomly pulls out an unassigned literal.
  ''' 
  # Randomly select unassigned variable followed by its sign.
  return random.choice([1,-1])*random.choice([x for x in range(1,num_of_variables+1) if assignment[x]==-1])

def select_variable():
  '''
  Returns:
      int: The selected literal according to the global variable strategy.
  ''' 
  if strategy == "ORD":
    return ORD()
  elif strategy == "LVS":
    return LVS()
  elif strategy == "RAN":
    return RAN()
  elif strategy == "DLIS":
    return DLIS()
  elif strategy == "JW":
    return JW()

"""### CDCL Algorithm
```
1. function CDCL
2.     while (true) do
3.         while (BCP() = “conflict”) do
4.             backtrack-level := Analyze-Conflict();
5.             if backtrack-level < 0 then return “Unsatisfiable”;
6.             BackTrack(backtrack-level);
7.         if ¬Decide() then return “Satisfiable”;
```

Ref: Daniel Kroening,Ofer Strichman: Decision Procedure
"""

def CDCL():
  '''
  The main driver function of the CDCL algorithm
  '''
  global current_level, branch_variable, propogation_history, branch_record, learnings, branches
  # While all variables are not assigned
  while not assignment_over():
    # First do unit propogation
    conflict = unit_propogation()
    if conflict is None:
      # If there is no conflict then we need to see if all variables are not
      # assigned if not we will branch by selecting a variable
      if assignment_over():
        break
      # Branching is happening
      branches = branches + 1
      # Select a variable to assign
      literal = select_variable()
      # As we are branching we will have to increase the level
      current_level += 1
      # Assign True to literal
      assignment[literal_value(literal)] = literal_sign(literal)
      # Now  as this is a branching point we need to store where we are
      # Branching off, will help later in conflict analyze
      branch_variable.add(literal_value(literal))
      branch_record[current_level] = literal_value(literal)
      # Also we will keep a record of all the unit propositions
      propogation_history[current_level] = OrderedSet()
      # Update the implication graph, by adding this node
      update_graph(literal_value(literal))
    else:
      # As a conflict has arised we call analyze conflict
      # From this we get learning (a clause learned) and a level to jump back to
      backtrack_level, learning = analyze_conflict(conflict)
      # If level is negative forumla is unsat
      if backtrack_level < 0:
        return False
      # Add clause to the global list
      learnings.add(learning)
      # backtrack and change current level
      backtrack(backtrack_level)
      current_level = backtrack_level
  return True

"""### Analyze Conflict Algorithm
```
1. if current-decision-level = 0 then return -1;
2. cl := current-conf licting-clause;
3. while (¬Stop-criterion-met(cl)) do
4.     lit := Last-assigned-literal(cl);
5.     var := Variable-of-literal(lit);
6.     ante := Antecedent(lit);
7.     cl := Resolve(cl, ante, var);
8. add-clause-to-database(cl);
9. return clause-asserting-level(cl)
```
Ref: Daniel Kroening,Ofer Strichman: Decision Procedure
"""

def analyze_conflict(conflict_clause):
  '''
  Args:
      clause ({int}): 
  Returns:
      int: Level we should jump back to
      {int}: Learned Clause
  '''
  # If conflict is at level 0 no solution is possible
  if current_level == 0:
    return -1,None

  # In current level the order in which variables were assigned
  assignment_order = [branch_record[current_level]] + list(propogation_history[current_level])

  currrent_conflicting_clause = conflict_clause

  # While we don't reach the first UIP we don't stop, and it will always
  # terminate as it is guranteed that first UIP will exist.
  while not stop_criterion_met(currrent_conflicting_clause):
    # Choose the most recent variable assignment done
    literal = choose_literal(currrent_conflicting_clause,assignment_order)
    # Find ante, the clause to which this literal belongs to
    ante = antecedent(literal_value(literal))
    # Resolution is done on ante and currently conflicting clause and update it
    currrent_conflicting_clause = resolve(currrent_conflicting_clause,ante,literal_value(literal))
  
  # Return Backtrack Level and Learned Clause from the conflicting clause
  return get_learnings_and_level(currrent_conflicting_clause)


def stop_criterion_met(clause):
  '''
  UIP will be the point where at a single level only one assignment is present. 
  Args:
      clause ({int}): 
  Returns:
      bool: If UIP is found return True
  '''
  current_level_literal = set()
  for literal in clause:
    if graph[literal_value(literal)].level == current_level:
      current_level_literal.add(literal)
  
  if len(current_level_literal) == 1:
  # We are at the UIP as only literal is at current level
    return True
  else:
    return False

def choose_literal(clause,assignment_order):
  '''
  Args:
      clause ({int}):
      assignment_order ([int]): 
  Returns:
      int: Chosen Literal
  '''
  # For literal in assignment order
  for literal in assignment_order[::-1]:
    if literal in clause or -literal in clause:
      return literal


def get_learnings_and_level(clause):
  '''
  Args:
      clause ({int}): 
  Returns:
      int: Backtrack Level
      {int}: Clause
  '''
  literals = set()
  backtrack_level = -1  
  # Backtrack Level will be the maximum level found of the given clause that are
  # not of current level, if none return current level - 1 
  for literal in clause:
    literals.add(literal)
    if graph[literal_value(literal)].level != current_level:
      backtrack_level = max(graph[literal_value(literal)].level,backtrack_level)

  if backtrack_level == -1:
    backtrack_level = current_level-1
  return backtrack_level,frozenset(literals)

def antecedent(variable):
  '''
  Return clause of the variable that is the ante
  Args:
      varaible (int): 
  Returns:
      {int}: Ante
  '''
  return graph[variable].clause

def resolve(clause,ante,literal):
  '''
  Args:
      clause ([int]):
      ante ([int]):
      literal (int):             
  Returns:
      {int}: Clause
  '''
  # We are doing resolution in this step.
  # (x+y')(y+z) => (x+z)
  return (clause.union(ante)).difference([literal,-literal])

def unit_propogation():
  '''
  Returns:
      {int}: conflict clause
  '''  
  global assignment,propogation_history, implications
  # Keep doing until unit clauses are present
  while True:
    # Create a OrderedSet for all the unit clauses encountered.
    # OrderedSet preserves insertion order and does quicker query 
    propogation = OrderedSet()
    for clause in [x for x in clauses.union(learnings)]:
      # Evaluate a clause, if satisfied continue, if unsatisfied report conflict
      # clause else add it to the propogation list
      result = evaluate_clause(clause)
      if result == 1:
        continue
      elif result == 0:
        return clause
      elif result == -1:
        propogation.add((get_first_literal(clause),clause))
    # If no unit clause is encountered return None
    if len(propogation) == 0:
      return None
    # Assign the variable and update the implication graph, add the assignment
    # to history of current level
    for literal,clause in propogation:
      # As this assignment is implied
      implications = implications + 1
      assignment[literal_value(literal)] = literal_sign(literal)
      update_graph(literal_value(literal),clause=clause)
      if current_level != 0:
        propogation_history[current_level].add(literal)


def backtrack(backtrack_level):
  '''
  Args:
      backtrack_level (int):
  '''
  global graph,assignment,propogation_history,branch_record,branch_variable
  # Iterate over all the nodes of the graph
  for variable, node in graph.items():
    # Node has level greater than backtrack level delete it, else keep it but 
    # delete children which have a level greater.
    if node.level <= backtrack_level:
      pruned_children = []
      for child in node.children:
        if child.level <= backtrack_level:
          pruned_children.append(child)
      node.children = pruned_children
    else:
      del node
      graph[variable] = Node(variable)
      assignment[variable] = -1

  # Remove bad literals from the list of branch variables
  branch_variable = {variable for variable in range(1,num_of_variables+1) if (assignment[variable] != -1 and len(graph[variable].parents) == 0)}

  # Remove the histories of larger levels.
  levels = list(branch_record.keys())
  for level in levels:
    if level > backtrack_level:
      del branch_record[level]
      del propogation_history[level]


def update_graph(variable, clause=None):
  '''
  Args:
      variable (int):
      clause ([int]):
  '''
  # Update the assignment and level of variable
  global graph
  graph[variable].level = current_level
  graph[variable].value = assignment[variable]

  # If over here by branching then there will be no clause, as it is selected by
  # us but in case of propogation, there will be clause due to which it is here.

  if clause is not None:
    # Update parents of the clause. As it was a unit clause all others will have
    # already being satisfied hence they will be parent to current node.
    for l_literal in clause:
      literal = literal_value(l_literal)
      if variable != literal:
        graph[literal].children.append(graph[variable])
        graph[variable].parents.append(graph[literal])
    graph[variable].clause = clause

def solve():
  '''
  Returns:
      [int]: Results
  ''' 
  initialize_solver()
  if CDCL():
    return True,"s SATISFIABLE\n" + " ".join(["v"]+[ str(-x) if assignment[x] == 0 else str(x) for x in range(1,num_of_variables+1)] + ["0"])
  else:
    return False,"s UNSATISFIABLE"

def terminal_solve(input_file,strategy="DLIS"):
  global num_of_variables,clauses
  num_of_variables,clauses = readFile(input_file)
  num_of_clauses = len(clauses)
  clauses = compressCNF(clauses)
  initialize_solver()
  x = time.time()
  output = CDCL()
  y = time.time()
  static = "c File: " + input_file + "\nc Clauses: " + str(num_of_clauses) + ", Variables: " + str(num_of_variables)+"\n" + "c Time: " + str(y-x)+"\nc Branches: " + str(branches) + " Implications: " + str(implications) + "\nc ================================= \n"
  if output:
    print(static +"s SATISFIABLE\n" + " ".join(["v"]+[ str(-x) if assignment[x] == 0 else str(x) for x in range(1,num_of_variables+1)] + ["0"]))
  else:
    print(static + "s UNSATISFIABLE")

result = []

def benchmark_solve(input_file):
  # Read The File, regularize and compress the clauses.
  global num_of_variables,clauses
  x = time.time()
  num_of_variables,clauses = readFile(input_file)
  num_of_clauses = len(clauses)
  clauses = compressCNF(clauses)
  y = time.time()
  global result
  result = [input_file,num_of_variables,num_of_clauses,"?",y-x]
  global strategy
  for st in strategies:
    strategy = st
    print(strategy)
    try:
      x = time.time()
      result[3],solution = solve()
      y = time.time()
      result += [y-x,branches,implications]
      with open("solutions/"+input_file.split("/")[-1]+"-"+strategy+".cnf","w") as f:
        f.write(solution+"\nc File:"+input_file+"\nc Branches:"+str(branches)+" Implications:"+str(implications)+" Time:"+str(y-x))
    except timeout_decorator.timeout_decorator.TimeoutError:
      result += [str(test_case_timeout)+"++",branches,implications]
  # Return Result Array.
  return result


# results = []
# FOLDER_NAME = "test_cases"
# # For all the files in folder add the result of each file to results array
# for file in os.listdir(FOLDER_NAME):
#     results.append(benchmark_solve(FOLDER_NAME+"/"+file))

parser = argparse.ArgumentParser()
parser.add_argument("file")
parser.add_argument("--strategy",choices=strategies,default="RAN",help="Select strategy for branching, by default Random is used.",required=False,)
args = parser.parse_args()

strategy = args.strategy
terminal_solve(args.file)