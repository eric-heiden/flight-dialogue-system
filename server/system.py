from dialogue.manager import Manager
from dialogue.field import Field
from qpx_database import QPXDatabase

Destination = Field("Destination", ["destination"])
Origin = Field("Origin", ["origin"])
DepartureDate = Field("DepartureDate", ["departureDate"])
NonStop = Field("NonStop", ["nonstop"])

DialogueManager = Manager(
    available_fields=[
        Destination,
        Origin,
        DepartureDate,
        NonStop
    ],
    minimal_fields=[
        Destination.name, Origin.name, DepartureDate.name
    ],
    database=QPXDatabase())