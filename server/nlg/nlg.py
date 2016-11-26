from collections import defaultdict
from typing import Union

from dialogue.field import Field
import random

from dialogue.manager import Manager
from nlg.results_verbalizer import verbalize

generic_what_questions = [
    "Can you please tell me your desired %s?",
    "Please tell me your desired %s.",
    "What is your desired %s?"
]

thanks = [
    "thanks", "thank you", "awesome", "excellent", "great", "good choice"
]

error = [
    "Oh no! ☹", "I am inconsolable... ☹", "I'm so sorry! ☹"
]


class Speaker:
    def __init__(self, manager: Manager):
        self.asked = defaultdict(int)  # counts how often a question has been asked before
        self.last_question = None  # Field
        self.manager = manager

    def generic(self, what: str, additions=[]) -> str:
        choices = list(map(lambda g: g % what, generic_what_questions)) + additions
        return random.choice(choices)

    def say_list(self, l: [str]) -> str:
        if len(l) == 0:
            return ''
        if len(l) == 1:
            return l[0]
        if len(l) == 2:
            return '{l[0]} and {l[1]}'.format(l=l)
        return ', '.join(l[:-2]) + ', ' + self.say_list(l[-2:])

    def ask(self, field: Field, expected: {str: int}) -> str:
        if field is None:
            return random.choice(error) + " I couldn't come up with another question."

        self.asked[field.name] += 1
        self.last_question = field

        hint = ""
        if expected is not None and len(expected) > 0:
            hint = " I found " + self.say_list(list(map(lambda x: '%i flights with %s = %s' % (x[1], field.name, x[0]), expected.items())))

        if field.name == "Origin":
            return self.generic("place of departure", [
                "Where do you want to fly from?",
                "From where do you want to fly?"
            ]) + hint
        if field.name == "Destination":
            return self.generic("destination", [
                "Where do you want to fly to?"
            ]) + hint
        if field.name == "DepartureDate":
            return self.generic("date of departure", [
                "When do you want to fly?"
            ]) + hint
        if field.name == "NonStop":
            return random.choice([
                "Do you want to fly non-stop?",
                "Do you want to avoid any intermediate stops?"
            ]) + hint
        return self.generic(field.name.lower()) + hint

    # give feedback for Manager.inform()
    def inform(self, feedback: (bool, Union[str,int])) -> [str]:
        success, data = feedback
        if success:
            if data is None or data <= 0:
                return [random.choice(thanks).capitalize() + "! " + random.choice([
                    "Now, before I can show you some flights I need more information.",
                    "Let me gather some more information until I can show you some flights."
                ])]
            return verbalize(self.manager.possible_data, 4)
        else:
            return [random.choice(error) + " I got a problem from my manager. He said \"%s\"." % data]
