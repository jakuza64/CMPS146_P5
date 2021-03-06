from heapq import heappush, heappop
import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        if rule.get('Consumes') != None:
            for item,value in rule['Consumes'].items():
                state_item = state.get(item)
                if state_item is None:
                    return False
                elif state_item < value:
                    return False
        if rule.get('Requires') != None:
            for elem,value in rule['Requires'].items():
                state_elem = state.get(elem)
                if state_elem is None:
                    return False
                elif state_elem < value:
                    return False
        return True

    return check


def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        next_state = state.copy()
        if rule.get('Consumes') != None:
            for item,value in rule['Consumes'].items():
                if item in next_state:
                    next_state[item] -= value
                    if next_state[item] == 0:
                        del next_state[item]
        if rule.get('Produces') != None:
            for item,value in rule['Produces'].items():
                if item in next_state:
                    next_state[item] += value
                else:
                    next_state[item] = value
        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        check = False
        for key in goal:
            for state_key in state:
                if state_key == key and state.get(state_key) >= goal.get(key):
                    check = True
            if check == False:
                return False
            check = False
        return True
        
    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)


def heuristic(state, action):
    # Implement your heuristic here!
    for item,value in state.items():
        if item[len(item)-3:] == 'axe' and value > 1:
            return 999
        elif item == 'bench' and value > 1:
            return 999
        elif item == 'cart' and value > 1:
            return 999
        elif item == 'furnace' and value > 1:
            return 999

        #This item has no utility
        elif item == 'iron_axe' and value > 0:
            return 999

    for recipe in all_recipes:
        if recipe.name == action:
            return recipe.cost

def search(graph, state, is_goal, limit, heuristic):

    start_time = time()

    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state
    frontier = []
    heappush(frontier, (0, state, 'start'))
    came_from = {}
    cost_so_far = {}
    came_from[state] = None
    cost_so_far[state] = 0
    
    while time() - start_time < limit and not len(frontier) == 0:

        curr_priority,current,current_action = heappop(frontier)
        
        if is_goal(current):
            print()
            print(time() - start_time, 'seconds.')
            print("Length of frontier: " + str(len(frontier)))
            print()
            
            final_list = []
            stuff = came_from[current]
            length = 0
            while stuff != None:
                length += 1
                final_list.append(stuff)
                stuff = came_from[stuff[0]]
                
            print()
            print (cost_so_far[current])
            print (length)
            print()

            return final_list

        gen = graph(current)
        for next in gen:
            new_cost = cost_so_far[current] + next[2]
            if cost_so_far.get(next[1]) == None or new_cost < cost_so_far[next[1]]:
                cost_so_far[next[1]] = new_cost
                priority = new_cost + heuristic(next[1], next[0])
                heappush(frontier, (priority, next[1], next[0]))
                came_from[next[1]] = (current,current_action)

    # Failed to find a path
    print(time() - start_time, 'seconds.')
    print("Duplicates: " + str(duplicates))
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('crafting.json') as f:
        Crafting = json.load(f)

    # List of items that can be in your inventory:
    print('All items:', Crafting['Items'])

    # List of items in your initial inventory with amounts:
    print('Initial inventory:', Crafting['Initial'])

    # List of items needed to be in your inventory at the end of the plan:
    print('Goal:',Crafting['Goal'])

    # Dict of crafting recipes (each is a dict):
    print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search for a solution
    resulting_plan = search(graph, state, is_goal, 30, heuristic)

    if resulting_plan:
        # Print resulting plan
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
