import sys, requests, uuid, json, os
from colorama import Fore


FOLDER_PREFIX = "qpx/"


def get_flights(request):
    try:
        key = "".join(open(FOLDER_PREFIX + "api.key", "r").readlines()).strip()
    except:
        key = None
    if key is None:
        print("Could not read QPX key from file \"api.key\".")
        sys.exit(1)
    # else:
    #     print("Using API key %s." % key)

    # search cache for query
    request_dump = json.dumps(request["request"], sort_keys=True)
    for base, _, files in os.walk(FOLDER_PREFIX + 'cache/'):
        for file in files:
            cached = json.load(open(os.path.join(FOLDER_PREFIX + "cache", file), "r"))
            # print(request_dump)
            # print(json.dumps(cached["request"], sort_keys=True))
            if "request" in cached and json.dumps(cached["request"], sort_keys=True) == request_dump:
                print(Fore.LIGHTBLACK_EX + "Found matching cache file %s." % file + Fore.BLACK)
                return cached["response"]

    r = requests.post(
        'https://www.googleapis.com/qpxExpress/v1/trips/search?fields=kind%2Ctrips&key=' + key,
        json=request)
    if r.status_code != 200:
        print(Fore.RED, r, Fore.WHITE)
    else:
        cache = request
        cache["response"] = r.json()
        json.dump(cache, open(FOLDER_PREFIX + "cache/%s.json" % str(uuid.uuid4()), "w"), indent=4)
        return r.json()
    return None


def extract_flights(response):
    if response is None:
        return None

    flights = []
    if "tripOption" not in response["trips"]:
        return flights
    for tripOption in response["trips"]["tripOption"]:
        if len(tripOption["slice"]) == 0:
            continue
        flight = {}
        flight["price"] = tripOption["saleTotal"]
        flight["slices"] = []
        flight["totalDuration"] = 0  # in minutes
        for slice in tripOption["slice"]:
            s = {}
            s["duration"] = slice["duration"]
            flight["totalDuration"] += slice["duration"]
            s["segments"] = []
            for si, segment in enumerate(slice["segment"]):
                seg = {}
                for p in ["cabin", "duration", "bookingCode", "bookingCodeCount", "flight"]:
                    seg[p] = segment[p]
                seg["connectionDuration"] = segment["connectionDuration"] if "connectionDuration" in segment else 0
                seg["legs"] = []
                for li, leg in enumerate(segment["leg"]):
                    l = leg
                    del l["kind"]
                    del l["id"]
                    seg["legs"].append(l)
                s["segments"].append(seg)

            flight["slices"].append(s)

        flights.append(flight)

    return flights


def stringify(flight):
    def get_origin(slice, p="origin"):
        return slice["segments"][0]["legs"][0][p]

    def get_destination(slice, p="destination"):
        return slice["segments"][-1]["legs"][-1][p]

    def intermediate_stops(flight, origin, destination):
        im = set()
        for slice in flight["slices"]:
            for segment in slice["segments"]:
                for leg in segment["legs"]:
                    if leg["origin"] != origin:
                        im.add(leg["origin"])
                    if leg["destination"] != destination:
                        im.add(leg["destination"])
        return list(im)

    def carriers(flight):
        cs = set()
        for slice in flight["slices"]:
            for segment in slice["segments"]:
                cs.add(segment["flight"]["carrier"])
        return list(cs)

    def stringify_list(l):
        s = ""
        if len(l) > 2:
            s = ", ".join(l[:-2]) + ", "
        if len(l) == 1:
            return l[0]
        else:
            return s + "%s and %s" % (l[-2], l[-1])

    origin = get_origin(flight["slices"][0])
    if len(flight["slices"]) == 2:
        destination = get_destination(flight["slices"][1])
        if origin == destination:
            destination = get_destination(flight["slices"][0])
        output = "Return Trip from %s to %s" % (origin, destination)
    else:
        destination = get_destination(flight["slices"][0])
        output = "%i-Way Trip from %s to %s" % (len(flight["slices"]), origin, destination)

    im = intermediate_stops(flight, origin, destination)
    if len(im) > 0:
        output += " over %s" % stringify_list(im)

    departure = get_origin(flight["slices"][0], "departureTime").replace("T", " ")
    arrival = get_destination(flight["slices"][-1], "arrivalTime").replace("T", " ")
    year_substring = len("YYYY-MM-DD")
    if departure[:year_substring] == arrival[:year_substring]:
        arrival = "the same day at %s" % arrival[year_substring + 1:]
    output += " departing on %s and arriving on %s" % (departure, arrival)
    output += " with %s" % stringify_list(carriers(flight))
    output += " for %s" % flight["price"].replace("USD", "$ ")

    return output


def main(argv):
    request = {
        "request": {
            "passengers": {
                "adultCount": 1
            },
            "slice": [
                {
                    "date": "2016-12-09",
                    "origin": "LAX",
                    "destination": "AMS"
                }
            ]
        }
    }

    flights = extract_flights(get_flights(request))
    # print(json.dumps(flights, indent=4))
    if len(flights) > 0:
        print(Fore.GREEN + "Found %i flights." % len(flights) + Fore.BLACK)
        for flight in flights:
            print(stringify(flight))
    else:
        print(Fore.RED + "Could not find any flights matching your query." + Fore.BLACK)


if __name__ == '__main__':
    main(sys.argv)
