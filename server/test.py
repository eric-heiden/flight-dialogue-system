from qpx import qpx
from dialogue.field import Field, NumField, NumCategory
import json, sys, re

# request = {
#         "request": {
#             "passengers": {
#                 "adultCount": 1
#             },
#             "slice": [
#                 {
#                     "date": "2016-12-09",
#                     "origin": "LAX",
#                     "destination": "LAS"
#                 }
#             ]
#         }
#     }
# flights = qpx.extract_flights(qpx.get_flights(request))
# json.dump(flights, open("flights.json", "w"), indent=4)
#
# price = NumField("Price",
#                  ["price"],
#                  [NumCategory("cheap", 0, 150),
#                   NumCategory("moderate", 150, 800),
#                   NumCategory("expensive", 800, sys.maxsize)],
#                  # parse price from string, e.g. "USD83.10"
#                  lambda raw: float(re.match(".*?([0-9\.]+)", raw).group(1)))
#
# # for flight in flights:
# #     print(price.filter(flight))
#
# price.print_stats(flights)
#
#
# legs = Field("Legs", ["legs"])
# legs.print_stats(flights)
# duration = Field("Duration", ["totalDuration"])
# duration.print_stats(flights)
# #print(duration.entropy(flights))
#
# destination = Field("Destination", ["destination"])
# destination.print_stats(flights)
# carrier = Field("Carrier", ["carriers"])
# carrier.print_stats(flights)
# cabin = Field("Cabin Class", ["cabins"])
# cabin.print_stats(flights)
# arrivalDate = Field("Arrival Date", ["arrivalDate"])
# arrivalDate.print_stats(flights)
# passengers = Field("Passengers", ["passengers"])
# passengers.print_stats(flights)

from system import DialogueManager
from nlg.nlg import Speaker

speaker = Speaker(DialogueManager)
print(speaker.ask(DialogueManager.next_question()[0]))
print(speaker.inform(DialogueManager.inform("Destination", [("AMS", 1)])))
print(speaker.ask(DialogueManager.next_question()[0]))
print(speaker.inform(DialogueManager.inform("Origin", [("LAX", 1)])))
print(speaker.ask(DialogueManager.next_question()[0]))
print(speaker.inform(DialogueManager.inform("DepartureDate", [])))
print(speaker.ask(DialogueManager.next_question()[0]))
print(speaker.inform(DialogueManager.inform("DepartureDate", [("2016-12-09", 1)])))
print(speaker.ask(DialogueManager.next_question()[0]))
