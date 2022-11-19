# This program needs as inputs (i) the path where you want to locate the destination folder (without the name of the destination folder),
# (ii) the path of the file or the folder containing all and only the files (.log) you want to compute.
# The output will be a folder at the specified path containing the .csv file generated.


import csv
import sys
import os
import pdb
import statistics


# Function for the creation the destination folder. Input: destination path. Return value: none.
def create_folder(path):

	if not path.endswith('/'):

		path = path + "/"

	path = path + "csv_rep_rules"

	try:

	    os.mkdir(path)

	except OSError:

	    print ("Creation of the directory %s failed" % path)

	else:

	    print ("Successfully created the directory %s " % path)
	    return path


# Function for obtaining the filename without folder and extension. Input: path of the file. Return value: file name.
def get_filename():

	return "rules.csv"


# Function for the generation of the header of the file. Input: file path. Return value: none. 
def add_header(filename):

	file = open(filename, 'w', encoding = 'utf-8')
	file.write("rule_id" + ";" + "rule_type" + ";" + "average" + ";" + "minimum" + ";" + "maximum" + ";" + "std_dev" + ";" + "counter" + ";")
	file.write("target" + ";" + "method" + ";" + "caller_1" + ";" + "caller_2" + "\n")
	file.close()


# Function for reading the content of a file. Input: source path, file name, data structure to modify. Return value: updated data structure.
def read_file(read_path, filename, data):

	path = read_path + filename		
	file = open(path, 'r', encoding = "utf-8")
	reader = csv.reader(file, delimiter = ";")
	file_data = []
	index = 0

	for row in reader:
		if index != 0:

			file_data.append(row)

		index += 1

	file.close()
	data.append(file_data)

	return data


def is_repetition_pattern(pattern):


	for i in range(0, len(pattern) - 1):
		if pattern[i][6] != pattern[i + 1][6] or pattern[i][7] != pattern[i + 1][7]:

			return False

	return True


# Function for writing the final file. Input: rules to be written, destination path. Return value: none.
def write_file(rules, write_path):

	if not write_path.endswith('/'):

		write_path = write_path + "/"

	add_header(write_path + get_filename())

	for rule in rules:
		write_rule(rule, write_path + get_filename())


# Function for writing a single rule. Input: rule id, rule type (ORD or OCC), rule accuracy, rule validity counter, rule coverage, 
# rule to be written, destination file name. Return value: none.
def write_rule(rule, filename):

	file = open(filename, 'a', encoding = 'utf-8')
	file.write(str(rule[0]) + ";" + rule[1] + ";" + str(rule[2]) + ";" + str(rule[3]) + ";" + str(rule[4]) + ";" + str(rule[5]) + ";" + str(rule[6]) + ";")
	file.write(rule[7] + ";" + rule[8] + ";" + rule[9] + ";" + rule[10] + "\n")
	file.close()


# Function for the directory processing. Input: source path, destination path, window size, threshold. Return value: none.
def process_directory(read_path, write_path):

	data = []

	for file in os.listdir(read_path):

		data = read_file(read_path, file, data)

	page_index = 0	
	rules = []
	patterns = []

	for page in data:

		rr_ids = []
		gr_ids = []

		for line in page:

			if len(line[0]) != 0:
				if int(line[0]) not in gr_ids:

					gr_ids.append(int(line[0]))

			if len(line[2]) != 0:
				if int(line[2]) not in rr_ids:

					rr_ids.append(int(line[2]))

		for pattern_id in gr_ids:

			pattern = []

			for line in page:
				if len(line[0]) != 0:
					if int(line[0]) == pattern_id:

						pattern.append(line)

			if is_repetition_pattern(pattern) and len(pattern) > 2:

				patterns.append((pattern[0], len(pattern), "G = R"))

		for pattern_id in rr_ids:

			pattern = []

			for line in page:
				if len(line[2]) != 0:
					if int(line[2]) == pattern_id:

						pattern.append(line)

			if is_repetition_pattern(pattern) and len(pattern) > 2:

				patterns.append((pattern[0], len(pattern), "R = R"))

		page_index += 1
		print("Processing file number ", page_index)

	found_patterns = []
	ids = []
	pattern_id = 0
	index = 0

	for pattern in patterns:

		ids.append(0)

	for pattern in patterns:

		found = False

		for element in found_patterns:
			if element[0] == pattern[0][6] and element[1] == pattern[0][7] and element[2] == pattern[2]:

				ids[index] = element[3]
				found = True
				break

		if not found:

			pattern_id += 1
			found_patterns.append((pattern[0][6], pattern[0][7], pattern[2], pattern_id))

		index += 1

	rules = []

	for i in range(1, pattern_id + 1):

		index = 0
		lengths = []
		rule_type = ""
		line = []

		for pattern in patterns:
			if ids[index] == i:

				lengths.append(pattern[1])
				rule_type = pattern[2]
				line = pattern[0]

			index += 1

		std_dev = statistics.stdev(lengths)
		average = statistics.mean(lengths)
		minimum = min(lengths)
		maximum = max(lengths)

		rules.append((i, rule_type, average, minimum, maximum, std_dev, len(lengths), line[6], line[7], line[10], line[11]))

	write_file(rules, write_path)
	print("Successfully created file: rules.csv")


write_path = sys.argv[1]
read_path = sys.argv[2]

write_path = create_folder(write_path)
path = read_path

if os.path.isdir(read_path):
	if not read_path.endswith('/'):

		path = read_path + "/"

	process_directory(path, write_path)
	
else:

	print("No such Directory")