import json
from enum import Enum
from typing import Union, Generator, Tuple

import sys, re

from qpx.qpx import stringify
from nlu.ResolveAirport import find_matches
# from nlu.nlu import extract_info
from dialogue.manager import Manager
from dialogue.field import Field, NumField, NumCategory
from nlg.nlg import Speaker
from nlg.results_verbalizer import verbalize
from qpx_database import QPXDatabase

OutputType = Enum('OutputType', 'greeting progress error feedback question finish')


class Output:
    def __init__(self, lines: [str] = [], output_type: Enum = OutputType.greeting):
        self.lines = lines
        self.output_type = output_type


class Pipeline:
    def __init__(self):
        Destination = Field("Destination", ["destination"])
        Origin = Field("Origin", ["origin"])
        DepartureDate = Field("Departure Date", ["departureDate"])
        ArrivalDate = Field("Arrival Date", ["arrivalDate"])
        NonStop = Field("NonStop", ["nonstop"])
        Price = NumField("Price",
                         ["price"],
                         [NumCategory("cheap", 0, 250),
                          NumCategory("moderate", 250, 1400),
                          NumCategory("expensive", 1400, sys.maxsize)],
                         # parse price from string, e.g. "USD83.10"
                         lambda raw: float(re.match(".*?([0-9\.]+)", raw).group(1)))
        Carrier = Field("Carrier", ["carriers"])
        Cabin = Field("Cabin Class", ["cabins"])
        self.manager = Manager(
            available_fields=[
                Destination,
                Origin,
                DepartureDate,
                ArrivalDate,
                NonStop,
                Price,
                Carrier,
                Cabin
            ],
            minimal_fields=[
                Destination.name, Origin.name, DepartureDate.name
            ],
            database=QPXDatabase())
        self.speaker = Speaker(self.manager)
        self.last_question = None
        self.expected_answer = None
        self.question_counter = 0

    def user_state(self) -> {str: [(Union[str, int, float], float)]}:
        return self.manager.user_state

    def generate_question(self):
        self.last_question, self.expected_answer = self.manager.next_question()
        self.question_counter += 1

    def show_status(self, status: Tuple[bool, Union[str, int]]) -> Generator[Output, None, None]:
        if status[1] is not None and status[1] == 1:
            yield Output(lines=["I found the perfect flight for you!"]
                               + verbalize(self.manager.possible_data, 2),
                         output_type=OutputType.finish)
        else:
            feedback = self.speaker.inform(status)
            yield Output(lines=feedback, output_type=OutputType.feedback)

    def interpret_statement(self, statement: {str: str}) -> Generator[Output, None, bool]:
        status = None
        direct_nlu_matches = {
            "out_date": "Departure Date",
            "in_date": "Arrival Date",
            "cabin_class": "Cabin Class",
        }
        for key, value in statement.items():
            if key == 'o_location' or key == 'o_entity':
                yield Output(lines=["Resolving origin airport code..."], output_type=OutputType.progress)
                airports = find_matches(value)
                status = yield from self.manager.inform("Origin", airports)
            elif key == 'd_location' or key == 'd_entity':
                yield Output(lines=["Resolving destination airport code..."], output_type=OutputType.progress)
                airports = find_matches(value)
                status = yield from self.manager.inform("Destination", airports)
            elif (key == 'u_location' or key == 'u_entity') and self.last_question.name in ["Origin", "Destination"]:
                which = self.last_question.name
                yield Output(lines=["Resolving %s airport code..." % which.lower()],
                             output_type=OutputType.progress)
                airports = find_matches(value[0])
                status = yield from self.manager.inform(which, airports)
            elif key in direct_nlu_matches:
                status = yield from self.manager.inform(direct_nlu_matches[key], [(value, 1)])
            elif key == "u_date" and self.last_question.name in ["Departure Date", "Arrival Date"]:
                status = yield from self.manager.inform(self.last_question.name, [(value, 1)])
            elif key == "airlines":
                airlines = []
                for airline in value:
                    airlines.append((airline, 1))
                status = yield from self.manager.inform("Carrier", airlines)

        if status is not None:
            yield from self.show_status(status)
            return True
        return False

    # matches utterance to expected values using fuzzy string matching
    def match_expected(self, utterance: str) -> [Tuple[str, float]]:
        from difflib import SequenceMatcher

        def score(a: str, b: str) -> float:
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        return list(map(lambda x: (x, score(utterance, x)), self.expected_answer.keys()))

    def input(self, utterance: str) -> Generator[Output, None, None]:
        if self.last_question is None:
            yield from self.output()

        yield Output(lines=["Loading NLU libraries..."],
                     output_type=OutputType.progress)
        from nlu.nlu import extract_info
        extracted = extract_info(utterance)
        utterance = utterance.lower()
        print('Utterance:', utterance)
        print('Extracted:', extracted)
        status = None

        if extracted["dialog_act"] == "statement":
            del extracted["dialog_act"]
            succeeded = yield from self.interpret_statement(extracted)
            if not succeeded:
                print('Failed to extract statement information from utterance. '
                      'Trying to recover by inferring context from last question.')
                if self.last_question is not None:
                    if self.last_question.name in ["Origin", "Destination"]:
                        which = self.last_question.name
                        yield Output(lines=["Resolving %s airport code..." % which.lower()],
                                     output_type=OutputType.progress)
                        airports = find_matches(utterance)
                        status = yield from self.manager.inform(which, airports)
                    else:
                        try:
                            matches = self.match_expected(utterance)
                            status = yield from self.manager.inform(self.last_question, matches)
                        except Exception as e:
                            print("Could not match to expected values.", e)
                            yield Output(lines=["Sorry, I didn't get that."],
                                         output_type=OutputType.error)

        elif self.last_question is not None:
            if extracted["dialog_act"] in ["yes", "no"]:
                print("YESNO")
                print(extracted)
                status = yield from self.manager.inform(self.last_question,
                                                        [(str(extracted["dialog_act"] == "yes"), 1)])

        if status is not None:
            yield from self.show_status(status)

        # if self.last_question.name == 'Origin' or self.last_question.name == 'Destination':
        #     yield Output(lines=["Resolving %s airport code..." % self.last_question.name], output_type=OutputType.progress)
        #     answer = find_matches(utterance)
        # else:
        #     answer = [(utterance, 1)]

        if status is not None and status[1] is not None and status[1] == 1:
            self.show_status(status)
            return

        self.generate_question()
        if self.last_question is None and len(self.manager.possible_data) > 0:
            # no problem, we have some flights but just ran out of questions
            json.dump({"data": self.manager.possible_data}, open("possible_data.json", "w"), indent=4)
            yield Output(
                lines=verbalize(self.manager.possible_data, 5),
                output_type=OutputType.finish)  # TODO finish is not quite right
        else:
            yield Output(
                lines=[self.speaker.ask(self.last_question, self.expected_answer)],
                output_type=OutputType.question)

    # Conversational output with no user input, and repeating last question
    def output(self) -> Generator[Output, None, None]:
        if self.question_counter == 0:
            self.generate_question()
            yield Output([
                "Hello!",
                "I'm your personal assistant to help you find the best flight 😊"
            ])
        yield Output(
            lines=[self.speaker.ask(self.last_question, self.expected_answer)],
            output_type=OutputType.question)
