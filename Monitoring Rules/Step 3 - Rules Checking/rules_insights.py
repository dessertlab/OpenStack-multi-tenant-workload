import csv
import sys
import os
import pdb


# Function for the creation the destination folder. Input: destination path. Return value: none.
def create_folder(path):

	if not path.endswith('/'):

		path = path + "/"

	path = path + "csv_RPC_to_REST_rules_insight"

	try:

	    os.mkdir(path)

	except OSError:

	    print ("Creation of the directory %s failed" % path)

	else:

	    print ("Successfully created the directory %s " % path)
	    return path


# Function for obtaining the filename without folder and extension. Input: path of the file. Return value: file name.
def get_filename():

	return "rules_insight.csv"


# Function for the generation of the header of the file. Input: file path. Return value: none. 
def add_header(filename):

	file = open(filename, 'w', encoding = 'utf-8')
	file.write("rule_id" + ";" + "rule_type" + ";" + "accuracy" + ";" + "valid_cnt" + ";" + "total_cnt" + ";")
	file.write("times_first" + ";" + "total_occs" + ";" + "target" + ";" + "method" + ";" + "global_request_id" + ";")
	file.write("request_id" + ";" + "caller_1" + ";" + "caller_2" + ";" + "status_code" + "\n")
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


def read_rules(path):

	file = open(path, 'r', encoding = "utf-8")
	reader = csv.reader(file, delimiter = ";")
	index = 0

	rules_data = []

	for row in reader:
		if index != 0:

			rules_data.append(row)

		index += 1

	rules = []
	temp_id = 0
	starter_line = []
	pattern = []
	index = 0

	for row in rules_data:
		
		if int(row[0]) != temp_id:

			starter_line = row
			temp_id = int(row[0])
			pattern = []

		else:

			pattern.append(row)

		if index == len(rules_data) - 1:

			rules.append((starter_line, pattern))

		elif temp_id != int(rules_data[index + 1][0]):

			rules.append((starter_line, pattern))

		index += 1

	return rules


def check_same_pattern(rule_pattern, pattern):

	if len(rule_pattern) < len(pattern):

		return False

	found = []
	used = []

	for i in range(0, len(rule_pattern)):

		found.append(False)

	for i in range(0, len(pattern)):

		used.append(False)

	rule_pattern_index = 0
	

	for rule_line in rule_pattern:

		pattern_index = 0

		for line in pattern:

			if rule_line[7] == line[6] and rule_line[8] == line[7] and used[pattern_index] is False:

				used[pattern_index] = True
				found[rule_pattern_index] = True
				break

			pattern_index += 1

		rule_pattern_index += 1

	for element in found:
		if not element:

			return False

	return True



def check_times_first(data, rules):

	times_first = []

	for rule in rules:

		counters = []

		if rule[0][1] == "ORD":
			for i in range(0, len(rule[1])):
				if i == 0:

					counters.append(int(rule[0][4]))

				else:

					counters.append(0)

		elif rule[0][1] == "OCC":

			for line in rule[1]:

				counters.append(0)

			for page in data:

				gr_ids = []
				rr_ids = []

				for line in page:
					if len(line[0]) != 0:
						if int(line[0]) not in gr_ids:

							gr_ids.append(int(line[0]))

					if len(line[2]) != 0:
						if int(line[2]) not in rr_ids:

							rr_ids.append(int(line[2]))

				patterns_gr = []
				patterns_rr = []

				for pattern_id in gr_ids:

					pattern = []

					for line in page:
						if len(line[0]) != 0:
							if int(line[0]) == pattern_id:

								pattern.append(line)

					patterns_gr.append(pattern)

				for pattern_id in rr_ids:

					pattern = []

					for line in page:
						if len(line[2]) != 0:
							if int(line[2]) == pattern_id:

								pattern.append(line)

					patterns_rr.append(pattern)

				for pattern in patterns_gr:
					if check_same_pattern(rule[1], pattern):

						line_index = 0

						for line in rule[1]:
							if line[7] == pattern[0][6] and line[8] == pattern[0][7]:

								counters[line_index] += 1

							line_index += 1

				for pattern in patterns_rr:
					if check_same_pattern(rule[1], pattern):

						line_index = 0

						for line in rule[1]:
							if line[7] == pattern[0][6] and line[8] == pattern[0][7]:

								counters[line_index] += 1

							line_index += 1

		times_first.append(counters)

	return times_first


def check_total_occs(data, rules):

	total_occs = []

	for rule in rules:

		counters = []

		for rule_line in rule[1]:

			counter = 0

			for page in data:
				for line in page:
					if len(line[8]) != 0:
						if rule_line[7] == line[6] and rule_line[8] == line[7]:

							counter += 1

			counters.append(counter)

		total_occs.append(counters)

	return total_occs

							
def write_file(path, rules, times_first, total_occs):

	if not path.endswith('/'):

		path = write_path + "/"

	add_header(path + get_filename())
	rule_id = 0

	for rule in rules:

		rule_id += 1
		write_rule(rule_id, rule, times_first[rule_id - 1], total_occs[rule_id - 1], path + get_filename())


# Function for writing a single rule. Input: rule id, rule type (ORD or OCC), rule accuracy, rule validity counter, rule coverage, 
# rule to be written, destination file name. Return value: none.
def write_rule(rule_id, rule, times_first, total_occs, filename):

	file = open(filename, 'a', encoding = 'utf-8')
	file.write(str(rule_id) + ";" + rule[0][1] + ";" + rule[0][2] + ";" + rule[0][3] + ";" + rule[0][4] + ";")
	file.write(";" + ";" + rule[0][7] + ";" + rule[0][8] + ";" + rule[0][9] + ";")
	file.write(rule[0][10] + ";" + rule[0][11] + ";" + rule[0][12] + ";" + rule[0][13] + "\n")

	event_index = 0

	for event in rule[1]:

		file.write(str(rule_id) + ";" + event[1] + ";" + event[2] + ";" + event[3] + ";" + event[4] + ";" + str(times_first[event_index]) + ";" + str(total_occs[event_index]) + ";")
		file.write(event[7] + ";" + event[8] + ";" + event[9] + ";" + event[10] + ";" + event[11] + ";" + event[12] + ";" + event[13] + "\n")
		event_index += 1

	file.close()


# Function for the directory processing. Input: source path, destination path, window size, threshold. Return value: none.
def process_directory(read_path_1, read_path_2, write_path):

	data = []

	for file in os.listdir(read_path_1):

		data = read_file(read_path_1, file, data)

	rules = read_rules(read_path_2)
	for rule in rules:
		print(rule)
	times_first = check_times_first(data, rules)
	total_occs = check_total_occs(data, rules)

	write_file(write_path, rules, times_first, total_occs)




write_path = sys.argv[1]
read_path_1 = sys.argv[2]
read_path_2 = sys.argv[3]

write_path = create_folder(write_path)
path_1 = read_path_1
path_2 = read_path_2

if os.path.isdir(read_path_1):
	if not read_path_1.endswith('/'):

		path_1 = read_path_1 + "/"

	process_directory(path_1, path_2, write_path)
	
else:

	print("No such Directory")