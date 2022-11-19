# This program needs as inputs (i) the path where you want to locate the destination folder (without the name of the destination folder),
# (ii) the path of the file or the folder containing all and only the files (.log) you want to compute, (iii) the value of the window size
# you want to use for this computation, (iv) the value of the threshold. 
# The output will be a folder at the specified path containing the .csv file generated.


import csv
import sys
import os
import pdb


# Function for the creation the destination folder. Input: destination path. Return value: none.
def create_folder(path):

	if not path.endswith('/'):

		path = path + "/"

	path = path + "csv_RPC_to_REST_rules"

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
	file.write("rule_id" + ";" + "rule_type" + ";" + "accuracy" + ";" + "valid_cnt" + ";" + "total_cnt" + ";")
	file.write("timestamp" + ";" + "duration" + ";" + "target" + ";" + "method" + ";" + "global_request_id" + ";")
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


# Function for determining if a line can be seen as a starter line. Input: line to evaluate. Return value: boolean value.
def is_rule_starter_line(line):

	if len(line[8]) != 0:

		return False

	elif line[7] != "GET":

		return True

	return False


# Function for the evaluation of the accuracy of an order rule. Input: pattern type (GR or RR), data structure containing all data, starter line of the rule,
# list of the RPC events of the rule, window size. Return value: validity counter of the rule, coverage of the rule. 
def check_order_ratio(pattern_type, data, events, starter_line, window_size):

	id_index = 0

	if pattern_type:

		id_index = 2

	counter = 0
	valid = 0
	page_index = 0

	for page in data:

		starter_lines = []
		line_index = 0
		ids = []

		for line in page:
			if line[6] == starter_line[6] and line[7] == starter_line[7]:

				starter_lines.append(line)

			if len(line[id_index]) != 0:
				if line[6] == events[0][6] and line[7] == events[0][7]:
					if check_order(pattern_type, page, events, 1, int(line[id_index]), line_index) and int(line[id_index]) not in ids:

						ids.append(int(line[id_index]))
						counter += 1

						for row in starter_lines:
							if int(row[4]) >= int(line[4]) - window_size and int(row[4]) <= int(line[4]):

								valid += 1
								break

			line_index += 1

		page_index += 1

	return valid, counter


# Recursive function for checking if a list of events is present in order inside a pattern. Input: pattern type (GR or RR), 
# data structure containing a single file data, current line, list of the RPC events of the rule, event index, window size, 
# pattern id, current index. Return value: boolean value. 
def check_order(pattern_type, page, events, event_index, pattern_id, starter_line_index):

	id_index = 0

	if pattern_type:

		id_index = 2

	if event_index == len(events):

		return True

	for i in range(starter_line_index + 1, len(page)):

		line = page[i]

		if len(line[id_index]) != 0:
			if int(line[id_index]) == pattern_id:
				if line[6] == events[event_index][6] and line[7] == events[event_index][7]:

					return check_order(pattern_type, page, events, event_index + 1, pattern_id, i)

	return False


# Function for the evaluation of the accuracy of an occurency rule. Input: pattern type (GR or RR), data structure containing all data,
# starter line of the rule, list of the RPC events of the rule, window size. Return value: validity counter of the rule, coverage of the rule. 
def check_occ_ratio(pattern_type, data, events, starter_line, window_size):

	id_index = 0

	if pattern_type:

		id_index = 2

	counter = 0
	valid = 0
	page_index = 0

	for page in data:

		starter_lines = []
		line_index = 0

		ids = []
		patterns = []

		for line in page:
			if line[6] == starter_line[6] and line[7] == starter_line[7]:

				starter_lines.append(line)

			if len(line[id_index]) != 0:
				if int(line[id_index]) not in ids:

					ids.append(int(line[id_index]))

			line_index += 1

		for pattern_id in ids:

			pattern = []

			for line in page:
				if len(line[id_index]) != 0:
					if int(line[id_index]) == pattern_id:

						pattern.append(line)

			patterns.append(pattern)

		for pattern in patterns:

			check = []
			used = []

			for event in events:

				check.append(False)

			for line in pattern:

				used.append(False)

			event_index = 0

			for event in events:

				pattern_line_index = 0

				for pattern_line in pattern:
					if pattern_line[6] == event[6] and pattern_line[7] == event[7] and not used[pattern_line_index]:

						check[event_index] = True
						used[pattern_line_index] = True
						break

					pattern_line_index += 1

				event_index += 1

			found = 0

			for item in check:
				if item:

					found += 1

			if found == len(events):

				counter += 1

				for line in starter_lines:
					if int(line[4]) >= int(pattern[0][4]) - window_size and int(line[4]) <= int(pattern[0][4]):

						valid += 1
						break

		page_index += 1

	return valid, counter


# Function for adding a rule to the rules data structure. Input: rules data structure, rule to add, rule type (ORD or OCC), 
# rule accuracy, rule validity counter, rule coverage. Return value: updated rules data structure.
def add_rule(rules, rule, rule_type, ratio, valid, counter):

	for element in rules:
		if element[0][0][6] == rule[0][6] and element[0][0][7] == rule[0][7]:
			if rule_type == "ORD" and element[1] == "ORD":
				if len(element[0][1]) == len(rule[1]):

					index = 0
					cnt = 0

					for event in element[0][1]:
						if event[6] == rule[1][index][6] and event[7] == rule[1][index][7]:

							cnt += 1

						index += 1

					if cnt == len(rule[1]):

						return rules

			elif rule_type == "OCC" and element[1] == "OCC":
				if len(element[0][1]) == len(rule[1]):

					check = []

					for item in rule[1]:

						check.append(False)

					index = 0

					for event in element[0][1]:
						for i in range(0, len(rule[1])):
							if event[6] == rule[1][i][6] and event[7] == rule[1][i][7] and not check[i]:

								check[i] = True
								break

					cnt = 0

					for item in check:
						if item:

							cnt += 1

					if cnt == len(rule[1]):

						return rules
	
	rules.append((rule, rule_type, ratio, valid, counter))

	return rules


# Function for writing the final file. Input: rules to be written, destination path. Return value: none.
def write_file(rules, write_path):

	if not write_path.endswith('/'):

		write_path = write_path + "/"

	add_header(write_path + get_filename())
	rule_id = 0

	for rule in rules:

		rule_id += 1
		write_rule(rule_id, rule[1], rule[2], rule[3], rule[4], rule[0], write_path + get_filename())


# Function for writing a single rule. Input: rule id, rule type (ORD or OCC), rule accuracy, rule validity counter, rule coverage, 
# rule to be written, destination file name. Return value: none.
def write_rule(rule_id, rule_type, accuracy, valid, counter, rule, filename):

	file = open(filename, 'a', encoding = 'utf-8')
	file.write(str(rule_id) + ";" + rule_type + ";" + str(accuracy) + ";" + str(valid) + ";" + str(counter) + ";")
	file.write(rule[0][4] + ";" + rule[0][5] + ";" + rule[0][6] + ";" + rule[0][7] + ";" + rule[0][8] + ";")
	file.write(rule[0][9] + ";" + rule[0][10] + ";" + rule[0][11] + ";" + rule[0][12] + "\n")

	for event in rule[1]:

		file.write(str(rule_id) + ";" + rule_type + ";" + str(accuracy) + ";" + str(valid) + ";" + str(counter) + ";" + event[4] + ";" + event[5] + ";")
		file.write(event[6] + ";" + event[7] + ";" + event[8] + ";" + event[9] + ";" + event[10] + ";" + event[11] + ";" + event[12] + "\n")
	
	file.close()


# Function for the directory processing. Input: source path, destination path, window size, threshold. Return value: none.
def process_directory(read_path, write_path, window_size, threshold):

	data = []

	for file in os.listdir(read_path):

		data = read_file(read_path, file, data)

	page_index = 0	
	rules = []

	for page in data:

		rules_rr = []
		rules_gr = []

		patterns_rr = []
		patterns_gr = []

		rr_ids = []
		gr_ids = []

		line_index = 0

		for line in page:
			if len(line[0]) != 0:
				if int(line[0]) not in gr_ids:

					gr_ids.append(int(line[0]))

			if len(line[2]) != 0:
				if int(line[2]) not in rr_ids:

					rr_ids.append(int(line[2]))

		for pattern_id in gr_ids:

			events = []

			for line in page:
				if len(line[0]) != 0:
					if int(line[0]) == pattern_id:

						events.append(line)

			patterns_gr.append(events)

		for pattern_id in rr_ids:

			events = []

			for line in page:
				if len(line[2]) != 0:
					if int(line[2]) == pattern_id:

						events.append(line)

			patterns_rr.append(events)

		for pattern in patterns_gr:

			starter_lines = []

			for line in page:
				if is_rule_starter_line(line) and int(line[4]) >= int(pattern[0][4]) - window_size and int(line[4]) < int(pattern[0][4]):

					starter_lines.append(line)

			rules_gr.append((starter_lines, pattern))

		for pattern in patterns_rr:

			starter_lines = []

			for line in page:
				if is_rule_starter_line(line) and int(line[4]) >= int(pattern[0][4]) - window_size and int(line[4]) < int(pattern[0][4]):

					starter_lines.append(line)

			rules_rr.append((starter_lines, pattern))

		for rule in rules_gr:
			for starter_line in rule[0]:

				valid, counter = check_order_ratio(False, data, rule[1], starter_line, window_size)
				ratio = valid / counter

				if ratio >= threshold and counter >= 28:

					rules = add_rule(rules, (starter_line, rule[1]), "ORD", ratio, valid, counter)

				valid, counter = check_occ_ratio(False, data, rule[1], starter_line, window_size)
				ratio = valid / counter

				if ratio >= threshold and counter >= 28:

					rules = add_rule(rules, (starter_line, rule[1]), "OCC", ratio, valid, counter)

		for rule in rules_rr:
			for starter_line in rule[0]:

				valid, counter = check_order_ratio(True, data, rule[1], starter_line, window_size)
				ratio = valid / counter

				if ratio >= threshold and counter >= 28:

					rules = add_rule(rules, (starter_line, rule[1]), "ORD", ratio, valid, counter)

				valid, counter = check_occ_ratio(True, data, rule[1], starter_line, window_size)
				ratio = valid / counter

				if ratio >= threshold and counter >= 28:

					rules = add_rule(rules, (starter_line, rule[1]), "OCC", ratio, valid, counter)

		page_index += 1
		print("Processed file number ", str(page_index))

	write_file(rules, write_path)
	print("Successfully created file: rules.csv")


write_path = sys.argv[1]
read_path = sys.argv[2]
window_size = sys.argv[3]
threshold = sys.argv[4]

write_path = create_folder(write_path)
path = read_path

if os.path.isdir(read_path):
	if not read_path.endswith('/'):

		path = read_path + "/"

	process_directory(path, write_path, int(window_size), float(threshold))
	
else:

	print("No such Directory")