from collections import defaultdict
from typing import Union

from dialogue.field import Field
import random

from dialogue.manager import Manager

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

    def ask(self, field: Field) -> str:
        if field is None:
            return random.choice(error) + " I couldn't come up with another question."

        self.asked[field.name] += 1
        self.last_question = field
        if field.name == "Origin":
            return self.generic("place of departure", [
                "Where do you want to fly from?",
                "From where do you want to fly?"
            ])
        if field.name == "Destination":
            return self.generic("destination", [
                "Where do you want to fly to?"
            ])
        if field.name == "DepartureDate":
            return self.generic("date of departure", [
                "When do you want to fly?"
            ])
        if field.name == "NonStop":
            return random.choice([
                "Do you want to fly non-stop?",
                "Do you want to avoid any intermediate stops?"
            ])
        return self.generic(field.name.lower())

    # give feedback for Manager.inform()
    def inform(self, feedback: (bool, Union[str,int])) -> str:
        success, data = feedback
        if success:
            if data is None or data <= 0:
                return random.choice(thanks).capitalize() + "! " + random.choice([
                    "Now, before I can show you some flights I need more information.",
                    "Let me gather some more information until I can show you some flights."
                ])
            return random.choice(thanks).capitalize() + "! " + random.choice([
                "I found %i flights so far matching your query.",
                "Now we have %i flights.",
                "My database gives us %i flights. Sounds great, doesn't it? 😎 Let's proceed..."
            ]) % data
        else:
            return random.choice(error) + " I got a problem from my manager. He said \"%s\"." % data
