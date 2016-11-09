import sys, requests, uuid, json


def main(argv):
    try:
        key = "".join(open("api.key", "r").readlines()).strip()
    except:
        key = None
    if key is None:
        print("Could not read QPX key from file \"api.key\".")
        sys.exit(1)
    else:
        print("Using API key %s." % key)

    request = {
     "request": {
      "passengers": {
       "adultCount": 1
      },
      "slice": [
       {
        "date": "2016-11-09",
        "origin": "LAX",
        "destination": "JFK"
       }
      ]
     }
    }

    r = requests.post(
        'https://www.googleapis.com/qpxExpress/v1/trips/search?fields=kind%2Ctrips&key=' + key,
        json=request)
    print(r.json())
    cache = request
    cache["response"] = r.json()
    json.dump(cache, open("cache/%s.json" % str(uuid.uuid4()), "w"), indent=4)

if __name__ == '__main__':
    main(sys.argv)