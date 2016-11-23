from swda import CorpusReader
import re

EQUIVALENT_TAGS = {'sd': 'statement',
				   'sv': 'statement',
				   'aa': 'yes',
				   'qy': 'question',
				   'ny': 'yes',
				   'qw': 'question',
				   'nn': 'no',
				   'qy^d': 'question',
				   'na': 'yes',
				   'qo': 'question',
				   'qh': 'question',
				   'ar': 'no',
				   'ng': 'no',
				   'fp': 'other',
				   'oo_co_cc': 'other',
				   '^g': 'question',
				   'aap_am': 'yes',
				   'qw^d': 'question',
				   'ft': 'other'}

def convert_tag(damsl_tag):
	if damsl_tag in EQUIVALENT_TAGS:
		return EQUIVALENT_TAGS[damsl_tag]
	else:
		return None

corpus = CorpusReader('swda')

output = ['@relation test',
		  '@attribute text string',
		  '@attribute tag {statement, question, yes, no, other}',
		  '@data']

for utt in corpus.iter_utterances():
	converted_tag = convert_tag(utt.damsl_act_tag())
	if converted_tag is not None:
		cleaned_text = re.sub('[^\w .?]', '', utt.text)
		output.append('"{}",{}'.format(cleaned_text, converted_tag))

with open('weka/training_data.arff', 'w') as f:
	f.write('\n'.join(output))