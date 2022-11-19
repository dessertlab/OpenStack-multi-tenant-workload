import csv
import sys
import os
import pdb


def create_folder(path):

	if not path.endswith('/'):

		path = path + "/"

	path = path + "csv_RPC_rules"

	try:

	    os.mkdir(path)

	except OSError:

	    print ("Creation of the directory %s failed" % path)

	else:

	    print ("Successfully created the directory %s " % path)
	    return path


def get_filename():

	return "rules.csv"


def add_header(filename):

	file = open(filename, 'w', encoding = 'utf-8')
	file.write("rule_id" + ";" + "rule_type" + ";" + "pattern_type" + ";" + "total_cnt" + ";")
	file.write("times_first" + ";" + "total_occs" + ";" + "target" + ";" + "method" + "\n")
	file.close()


def read_file(src_path, filename, data):

	path = src_path + filename		
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


def check_order(pattern, patterns):

	counter = 0

	for element in patterns:

		pattern_index = 0

		for line in element:
			if line[6] == pattern[pattern_index][6] and line[7] == pattern[pattern_index][7]:

				pattern_index += 1

				if pattern_index == len(pattern):

					counter += 1
					break

	return counter


def check_occ(pattern, patterns):

	counter = 0

	for element in patterns:

		used = []
		check = []

		for line in element:

			used.append(False)

		for row in pattern:

			check.append(False)

		i = 0

		for row in pattern:

			j = 0

			for line in element:
				if row[6] == line[6] and row[7] == line[7] and not used[j] and not check[i]:

					used[j] = True
					check[i] = True
					break

				j += 1

			i += 1

		check_counter = 0

		for item in check:
			if item:

				check_counter += 1

		if check_counter == len(pattern):

			counter += 1

	return counter


def add_rule(rules, pattern, counter, pattern_type, rule_type):

	if len(rules) == 0:

		rules.append((pattern, counter, pattern_type, rule_type))
		return rules

	found = False

	for rule in rules:

		check = []
		used = []

		for line in rule[0]:

			used.append(False)

		for row in pattern:

			check.append(False)

		if rule_type == "ORD" and rule[3] == "ORD":
			if pattern_type == rule[2] and len(pattern) == len(rule[0]):
				for i in range(0, len(pattern)):
					if pattern[i][6] == rule[0][i][6] and pattern[i][7] == rule[0][i][7]:

						check[i] = True

				check_counter = 0

				for item in check:
					if item:

						check_counter += 1

				if check_counter == len(pattern):

					found = True
					break

		elif rule_type == "OCC" and rule[3] == "OCC":
			if pattern_type == rule[2] and len(pattern) == len(rule[0]):

				i = 0

				for row in pattern:

					j = 0

					for line in rule[0]:
						if row[6] == line[6] and row[7] == line[7] and not used[j] and not check[i]:

							used[j] = True
							check[i] = True
							break


						j += 1

					i += 1

				check_counter = 0

				for item in check:
					if item:

						check_counter += 1

				if check_counter == len(pattern):

					found = True
					break


	if not found:

		rules.append((pattern, counter, pattern_type, rule_type))

	return rules



def check_same_pattern(rule_pattern, pattern):

	if len(rule_pattern) > len(pattern):

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

			if rule_line[6] == line[6] and rule_line[7] == line[7] and used[pattern_index] is False:

				used[pattern_index] = True
				found[rule_pattern_index] = True
				break

			pattern_index += 1

		rule_pattern_index += 1

	for element in found:
		if not element:

			return False

	return True


def get_insight(data, rule, patterns):

	insights = []

	if rule[3] == "ORD":

		index = 0

		for row in rule[0]:

			counter = 0
			times_first = 0

			if index == 0:

				times_first = rule[1]

			for page in data:
				for line in page:
					if line[6] == row[6] and line[7] == row[7]:

						counter += 1

			insights.append((counter, times_first))

			index += 1

	else:
		for row in rule[0]:

			counter = 0
			times_first = 0

			for page in data:
				for line in page:
					if line[6] == row[6] and line[7] == row[7]:

						counter += 1

			for pattern in patterns:
				if check_same_pattern(rule[0], pattern):
					if pattern[0][6] == row[6] and pattern[0][7] == row[7]:

						times_first += 1

			insights.append((counter, times_first))

	return insights


def write_file(dest_path, rules_insight):

	if not dest_path.endswith('/'):

		dest_path = dest_path + "/"

	add_header(dest_path + get_filename())
	rule_id = 0

	for insight in rules_insight:

		rule_id += 1
		write_rule(rule_id, insight[0], insight[1], dest_path + get_filename())


def write_rule(rule_id, rule, insights, dest_path):

	file = open(dest_path, 'a', encoding = 'utf-8')

	for i in range(0, len(rule[0])):

		file.write(str(rule_id) + ";" + rule[3] + ";" + rule[2] + ";" + str(rule[1]) + ";")
		file.write(str(insights[i][1]) + ";" + str(insights[i][0]) + ";" + rule[0][i][6] + ";" + rule[0][i][7] + "\n")

	file.close()






def process_directory(src_path, dest_path):

	data = []

	for file in os.listdir(src_path):

		data = read_file(src_path, file, data)

	page_index = 0	
	rules = []
	gr_patterns = []
	rr_patterns = []	

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

		for pattern_id in gr_ids:

			pattern = []

			for line in page:
				if len(line[0]) != 0:
					if int(line[0]) == pattern_id:

						pattern.append(line)

			gr_patterns.append(pattern)

		for pattern_id in rr_ids:

			pattern = []

			for line in page:
				if len(line[2]) != 0:
					if int(line[2]) == pattern_id:

						pattern.append(line)

			rr_patterns.append(pattern)

		page_index += 1

	rules = []

	for pattern in gr_patterns:

		counter = check_order(pattern, gr_patterns)

		if counter >= len(data) / 2:

			rules = add_rule(rules, pattern, counter, "G=R", "ORD")

		counter = check_occ(pattern, gr_patterns)

		if counter >= len(data) / 2:

			rules = add_rule(rules, pattern, counter, "G=R", "OCC")

	for pattern in rr_patterns:

		counter = check_order(pattern, rr_patterns)

		if counter >= len(data) / 2:

			rules = add_rule(rules, pattern, counter, "R=R", "ORD")

		counter = check_occ(pattern, rr_patterns)

		if counter >= len(data) / 2:

			rules = add_rule(rules, pattern, counter, "R=R", "OCC")

	rules_insight = []

	for rule in rules:
		if rule[2] == "G=R":
		
			rules_insight.append((rule, get_insight(data, rule, gr_patterns)))

		else:

			rules_insight.append((rule, get_insight(data, rule, rr_patterns)))

	write_file(dest_path, rules_insight)


dest_path = sys.argv[1]
src_path = sys.argv[2]

dest_path = create_folder(dest_path)

if os.path.isdir(src_path):
	if not src_path.endswith('/'):

		src_path = src_path + "/"

	process_directory(src_path, dest_path)
	
else:

	print("No such Directory")