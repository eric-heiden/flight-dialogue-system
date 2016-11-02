import sys, json, requests, subprocess, time, numbers
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from colorama import Fore

FUZZ_RATIO = 0.2

resolved = False

available_options = json.load(open("airports.json", "r"))

column_scores = {
	"Name": 1.,
	"City": 0.5,
	"Country": 0.3,
	"IATA_FAA": 1.2,
	"ICAO": 1.5
}


# similarity score between 0 and 1
def score(a, b):
	# fuzz.partial_ratio(a, b) / 100. #
	return SequenceMatcher(None, a, b).ratio()

def find_matches(query):
	query = query.lower()
	matches = []
	for row in available_options:
		row_score = 0
		row_multiplier = 1. # higher weights for airports with IATA_FAA or ICAO number
		applicable_values = 0
		for key, value in row.items():
			if key == "ICAO" and value is None:
				row_multiplier *= 0.05
			if key == "IATA_FAA" and value is None:
				row_multiplier *= 0.05
			if key not in ["Name", "City", "Country", "IATA_FAA", "ICAO"]:
				continue
			if value is None or isinstance(value, numbers.Number):
				continue
			value = value.lower()
			column_score = column_scores[key]
			row_score += score(value, query) * column_score
			# equivalent partial matches:
			for word in query.split():
				if word in value:
					#print("Partial match between %s and %s" % (value, query))
					row_score += 1.5 / len(query.split()) * column_score
			applicable_values += 1.
		row_score *= row_multiplier / applicable_values
		if applicable_values > 0 and row_score > FUZZ_RATIO:
			matches.append((row_score, row))
	return sorted(matches, key=lambda entry: entry[0], reverse=True)

def main(argv):
	global resolved

	query = input("What fact do you know about the airport? ")
	matches = find_matches(query)
	if len(matches) == 0:
		print(Fore.RED + "Found no matches." + Fore.WHITE)
	elif len(matches) <= 10:
		print("The airport is %s." % " or ".join([row[1]["Name"] for row in matches]))
	else:
		print("Found %i matches." % len(matches))
		print("Top 10 matches are:\n\t%s" % "\n\t".join(["%.3f %s" % (row[0], row[1]["Name"]) for row in matches[:10]]))
	if len(matches) >= 2:
		# print most likely airport if the score is much better than the second best
		if matches[0][0] - matches[1][0] > 0.2:
			print(Fore.GREEN + "You probably mean %s (%s)." % (matches[0][1]["Name"], matches[0][1]["IATA_FAA"] or matches[0][1]["ICAO"]) + Fore.WHITE)

	#while not resolved:



if __name__ == "__main__":
    main(sys.argv)
