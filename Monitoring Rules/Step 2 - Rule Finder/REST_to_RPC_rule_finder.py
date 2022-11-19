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

	path = path + "csv_REST_to_RPC_rules"

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
def check_order_ratio(pattern_type, data, starter_line, events, window_size):

	counter = 0
	valid = 0
	id_index = 0

	if pattern_type:

		id_index = 2

	for page in data:

		index = 0

		for line in page:
			if is_rule_starter_line(line):
				if line[6] == starter_line[6] and line[7] == starter_line[7]:

					counter += 1

					if check_order(pattern_type, page, line, events, 0, window_size, 0, index):
						
						valid += 1

			index += 1

	return valid, counter


# Recursive function for checking if a list of events is present in order inside a pattern. Input: pattern type (GR or RR), 
# data structure containing a single file data, current line, list of the RPC events of the rule, event index, window size, 
# pattern id, current index. Return value: boolean value. 
def check_order(pattern_type, page, line, events, event_index, window_size, pattern_id, index):

	id_index = 0

	if pattern_type:

		id_index = 2

	if event_index == len(events):

		return True

	if event_index == 0:
		for i in range(index + 1, len(page)):
			if int(line[4]) + window_size > int(page[i][4]):
				if events[event_index][6] == page[i][6] and events[event_index][7] == page[i][7]:
					if len(page[i][id_index]) != 0:

						return check_order(pattern_type, page, page[i], events, event_index + 1, window_size, page[i][id_index], i)
			
			else:

				break

	else:
		for i in range(index + 1, len(page)):
			if page[i][id_index] == pattern_id and page[i][7] == events[event_index][7] and page[i][6] == events[event_index][6]:
				
				return check_order(pattern_type, page, page[i], events, event_index + 1, window_size, pattern_id, i)
	
	return False


# Function for the evaluation of the accuracy of an occurency rule. Input: pattern type (GR or RR), data structure containing all data,
# starter line of the rule, list of the RPC events of the rule, window size. Return value: validity counter of the rule, coverage of the rule. 
def check_occ_ratio(pattern_type, data, starter_line, events, window_size):
	id_index = 0

	if pattern_type:

		id_index = 2

	counter = 0
	valid = 0

	for page in data:

		index = 0

		for line in page:
			if is_rule_starter_line(line) and line[7] == starter_line[7] and line[6] == starter_line[6]:
				
				counter += 1
				ids = []
				
				for i in range(index + 1, len(page)):
					if int(line[4]) + window_size > int(page[i][4]):						
						if len(page[i][id_index]) != 0 and int(page[i][id_index]) not in ids:
							
							ids.append(int(page[i][id_index]))
					
					else:
						
						break
				
				patterns = []

				for element in ids:

					pattern = []

					for row in page:
						if len(row[id_index]) != 0:
							if int(row[id_index]) == element:

								pattern.append(row)		
					
					patterns.append(pattern)

				for pattern in patterns:

					found = 0

					for event in events:
						for row in pattern:
							if event[7] == row[7] and event[6] == row[6]:

								found += 1
								break

						if found == len(events):

							valid += 1
							break

			index += 1

	return valid, counter


# Function for adding a rule to the rules data structure. Input: rules data structure, rule to add, rule type (ORD or OCC), 
# rule accuracy, rule validity counter, rule coverage. Return value: updated rules data structure.
def add_rule(rules, rule, rule_type, ratio, valid, counter):

	for element in rules:
		if element[0][0][6] == rule[0][6] and element[0][0][7] == rule[0][7]:
			if rule_type == "ORD":
				if len(element[0][1]) == len(rule[1]):

					index = 0
					cnt = 0

					for event in element[0][1]:
						if event[6] == rule[1][index][6] and event[7] == rule[1][index][7]:

							cnt += 1

						index += 1

					if cnt == len(rule[1]):

						return rules

			elif rule_type == "OCC":
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

		line_index = 0

		for line in page:
			if is_rule_starter_line(line):

				rr_ids = []
				gr_ids = []

				for i in range(line_index + 1, len(page)):
					if int(line[4]) + window_size > int(page[i][4]):
						if len(page[i][0]) != 0 and int(page[i][0]) not in gr_ids:

							gr_ids.append(int(page[i][0]))

						elif len(page[i][2]) != 0 and int(page[i][2]) not in rr_ids:

							rr_ids.append(int(page[i][2]))

					else:

						break

				rules_gr = []
				rules_rr = []

				for pattern in gr_ids:

					events = []
					successive = True

					for row in page:
						if len(row[0]) != 0:
							if int(row[0]) == pattern:
								if int(row[4]) < int(line[4]):

									successive = False
									break

								events.append(row)

					same = True

					for i in range(0, len(events) - 1):
						if events[i][6] != events[i + 1][6] or events[i][7] != events[i + 1][7]:

							same = False

					if not same and successive:
						
						rules_gr.append((line, events))

				for pattern in rr_ids:

					events = []
					successive = True

					for row in page:
						if len(row[2]) != 0:
							if int(row[2]) == pattern:
								if int(row[4]) < int(line[4]):

									successive = False
									break

								events.append(row)

					same = True

					for i in range(0, len(events) - 1):

						if events[i][6] != events[i + 1][6] or events[i][7] != events[i + 1][7]:

							same = False

					if not same and successive:

						rules_rr.append((line, events))

				for rule in rules_gr:

					valid, counter = check_order_ratio(False, data, rule[0], rule[1], window_size)
					ratio = valid / counter

					if ratio >= threshold and counter >= 2:

						rules = add_rule(rules, rule, "ORD", ratio, valid, counter)

					else: 

						valid, counter = check_occ_ratio(False, data, rule[0], rule[1], window_size)
						ratio = valid / counter

						if ratio >= threshold and counter >= 2:

							rules = add_rule(rules, rule, "OCC", ratio, valid, counter)

				for rule in rules_rr:

					valid, counter = check_order_ratio(True, data, rule[0], rule[1], window_size)
					ratio = valid / counter

					if ratio >= threshold and counter >= 2:

						rules = add_rule(rules, rule, "ORD", ratio, valid, counter)

					else: 

						valid, counter = check_occ_ratio(True, data, rule[0], rule[1], window_size)
						ratio = valid / counter

						if ratio >= threshold and counter >= 2:

							rules = add_rule(rules, rule, "OCC", ratio, valid, counter)

			line_index += 1

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