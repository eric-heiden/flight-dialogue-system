# act_classifier.py

import glob
import subprocess


weka_jar_path = glob.glob('**/weka.jar', recursive=True)[0]
utterance_path = glob.glob('**/utterance.arff', recursive=True)[0]
model_path = glob.glob('**/j48.model', recursive=True)[0]


cmd = ' '.join([
	'java', '-cp', weka_jar_path,
	'weka.classifiers.trees.J48', '-T', utterance_path,
	'-l', model_path, '-p', '0'
])


def prepare_arff(utterance):
	output = ['@relation test',
			  '@attribute text string',
			  '@attribute tag {statement, question, yes, no, other}',
			  '@data']
	output.append('"{}",?'.format(utterance))
	with open(utterance_path, 'w') as f:
		f.write('\n'.join(output))


def classify(utterance):
	prepare_arff(utterance)
	results = subprocess.getoutput(cmd)
	tag = results.split()[13].split(':')[1].strip()
	return tag

def simple_classify(utterance):
	if 'yes' in utterance.lower():
		return 'yes'
	elif 'no' in utterance.lower():
		return 'no'
	elif '?' in utterance:
		return 'question'
	else:
		return 'statement'