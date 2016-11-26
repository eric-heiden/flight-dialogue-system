from enum import Enum
from typing import Union, Generator

import sys, re

from qpx.qpx import stringify
from dialogue.manager import Manager
from dialogue.field import Field, NumField, NumCategory
from nlg.nlg import Speaker
from nlg.results_verbalizer import verbalize
from qpx_database import QPXDatabase
#from nlu.nlu import extract_info
from nlu.ResolveAirport import find_matches

OutputType = Enum('OutputType', 'greeting progress feedback question askconfirm finish')


class Output:
    def __init__(self, lines: [str] = [], output_type: Enum = OutputType.greeting):
        self.lines = lines
        self.output_type = output_type


class Pipeline:
    def __init__(self):
        Destination = Field("Destination", ["destination"])
        Origin = Field("Origin", ["origin"])
        DepartureDate = Field("DepartureDate", ["departureDate"])
        ArrivalDate = Field("Arrival Date", ["arrivalDate"])
        NonStop = Field("NonStop", ["nonstop"])
        Price = NumField("Price",
                ["price"],
                [NumCategory("cheap", 0, 150),
                 NumCategory("moderate", 150, 800),
                 NumCategory("expensive", 800, sys.maxsize)],
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

    def user_state(self) -> {str: [(Union[str,int,float], float)]}:
        return self.manager.user_state

    def generate_question(self):
        self.last_question, self.expected_answer = self.manager.next_question()
        self.question_counter += 1

    def input(self, utterance: str) -> Generator[Output, None, None]:
        if self.last_question is None:
            yield from self.output()
        if self.last_question.name == 'Origin' or self.last_question.name == 'Destination':
            yield Output(lines=["Resolving %s airport code..." % self.last_question.name], output_type=OutputType.progress)
            answer = find_matches(utterance)
        else:
            answer = [(utterance, 1)]
        #  self.manager.onDatabaseQuerying.append(lambda: yield Output())
        status = yield from self.manager.inform(self.last_question, answer)
        if status[1] is not None and status[1] == 1:
            yield Output(lines=[
                "I found the perfect flight for you!"
            ] + verbalize(self.manager.possible_data, 1),
            output_type=OutputType.finish)
            return
        else:
            feedback = self.speaker.inform(status)
            yield Output(lines=feedback, output_type=OutputType.feedback)

        self.generate_question()
        if self.last_question is None and len(self.manager.possible_data) > 0:
            # no problem, we have some flights but just ran out of questions
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
