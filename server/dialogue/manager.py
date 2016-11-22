from collections import namedtuple
from typing import Union

import sys

from dialogue.database import Database
from dialogue.field import Field

MAX_DATA = 2500


DialogueTurn = namedtuple("DialogueTurn", ["type", "data"])


class Manager:
    # constructs dialogue manager using all available attributes and names of
    # the minimal attributes to generate a query to the knowledge base
    def __init__(self, available_fields: [Field], minimal_fields: [str], database: Database):
        self.available_fields = {}
        for field in available_fields:
            self.available_fields[field.name] = field

        self.minimal_fields = minimal_fields
        self.user_state = {} # {str: [(Union[str,int,float], float)]}
        self.database = database

        self.possible_data = [] # [object]

        self.interaction_sequence = []

    # determines whether the minimal fields have been completed
    def sufficient(self) -> bool:
        for f in self.minimal_fields:
            if f not in self.user_state:
                return False
        return True

    # returns attribute name + expected values
    def next_question(self) -> (Field, [Union[str,int,float]]):
        # first complete the minimal fields (if they haven't been filled)
        for name in self.minimal_fields:
            if name not in self.user_state:
                self.interaction_sequence.append(
                    DialogueTurn("question", name)
                )
                return self.available_fields[name], None

        # if we have data, choose best question based on scored entropy
        fields = list(self.available_fields.values())
        best_field = None
        best_entropy = sys.maxsize
        for field in fields[1:]:
            entropy = field.entropy(self.possible_data)
            if 1e-10 < entropy < best_entropy:
                best_entropy = entropy
                best_field = field

        if best_field is None:
            return None, None

        self.interaction_sequence.append(
            DialogueTurn("question", best_field.name)
        )
        return best_field, list(best_field.category_count(self.possible_data).keys())

    # provides information via attribute name + values with confidence scores
    # returns False, error message if something went wrong
    # otherwise True, number of possible flights
    def inform(self, attribute: str, values: [(str, float)]) -> (bool, Union[str,int]):
        self.interaction_sequence.append(
            DialogueTurn("answer", (attribute, values))
        )
        if len(values) == 0:
            return False, 'no attribute values provided'
        if len(values) > 1:
            pruned = self.available_fields[attribute].prune(values)
            print('Pruned %i values to %i.' % (len(values), len(pruned)))
            values = pruned
        self.user_state[attribute] = values

        return True, self.update()

    # provides feedback to a question which updates the attribute's score
    def feedback(self, attribute: str, positive: bool):
        self.interaction_sequence.append(
            DialogueTurn("feedback", (attribute, positive))
        )
        self.available_fields[attribute].score *= 1.1 if positive else 0.9
        pass

    # updates and returns number of possible flights
    # returns None if the minimal set of attributes has not been filled so far
    def update(self) -> int:
        if not self.sufficient():
            return None

        self.possible_data.clear()

        query_items = self.user_state.items()
        # keeps track of current index of value to query per attribute
        open_queries = [(attribute, len(values)-1) for attribute, values in query_items]
        while all(index >= 0 for _, index in open_queries):
            query = {}
            for attribute, index in open_queries:
                query[attribute] = self.user_state[attribute][index][0]
            self.possible_data += self.database.query(query)
            if len(self.possible_data) > MAX_DATA:
                break
            updated = False
            for i, (attribute, index) in enumerate(open_queries):
                if not updated and index > 0:
                    open_queries[i] = attribute, index-1
                    updated = True
                    break
            if not updated:
                break

        return len(self.possible_data)
