import csv
import sys
import os
import pdb
import bz2
import datetime


def create_folder(path):

	if not path.endswith('/'):

		path = path + "/"

	path = path + "anomalies"

	try:

	    os.mkdir(path)

	except OSError:

	    print ("Creation of the directory %s failed" % path)

	else:

	    print ("Successfully created the directory %s " % path)
	    return path


def get_filename():

	return "report.txt"


def read_file(src_path):

	file = open(src_log_path, 'r', encoding = 'utf-8')
	reader = csv.reader(file, delimiter = ";")
	index = 0
	data = []

	for row in reader:
		if index != 0:

			data.append(row)

		index = index + 1

	return data


def read_rules(src_path):

	file = open(src_path, 'r', encoding = 'utf-8')
	reader = csv.reader(file, delimiter = ";")
	index = 0
	data = []

	for row in reader:
		if index != 0:

			data.append(row)

		index += 1

	ord_rules = []
	fixed_start_occ_rules = []
	unfixed_start_occ_rules = []
	rule_index = 0
	starter_line = []
	pattern = []
	index = 0
	row_index = 0

	for row in data:
		if row_index != int(row[0]):

			row_index = int(row[0])
			starter_line = row
			pattern = []

		else:

			pattern.append(row)

		if index == len(data) - 1:
			if pattern[0][1] == "ORD":

				ord_rules.append((starter_line, pattern))

			else:
				fixed = True

				for line in pattern:
					if int(line[4]) == 0:

						fixed = False
						break

				if fixed:

					fixed_start_occ_rules.append((starter_line, pattern))

				else:

					unfixed_start_occ_rules.append((starter_line, pattern))


		elif row_index != int(data[index + 1][0]):
			if pattern[0][1] == "ORD":

				ord_rules.append((starter_line, pattern))

			else:
				fixed = True

				for line in pattern:
					if int(line[4]) == 0:

						fixed = False
						break

				if fixed:

					fixed_start_occ_rules.append((starter_line, pattern))

				else:

					unfixed_start_occ_rules.append((starter_line, pattern))
						
		index += 1

	return ord_rules, fixed_start_occ_rules, unfixed_start_occ_rules


def read_rep_rules(src_path):

	file = open(src_path, 'r', encoding = 'utf-8')
	reader = csv.reader(file, delimiter = ";")
	index = 0
	data = []

	for row in reader:
		if index != 0:

			data.append(row)

		index += 1

	rep_rules = []

	for row in data:

		rep_rules.append((row[4], row[5], row[2], row[3], row[1]))

	return rep_rules


def read_RPC_rules(src_path):

	file = open(src_path, 'r', encoding = 'utf-8')
	reader = csv.reader(file, delimiter = ";")
	index = 0
	data = []

	for row in reader:
		if index != 0:

			data.append(row)

		index += 1

	ord_rules = []
	fixed_start_occ_rules = []
	unfixed_start_occ_rules = []
	rule_index = 0
	pattern = []
	index = 0
	row_index = 0

	for row in data:
		if row_index != int(row[0]):

			row_index = int(row[0])
			pattern = []
			pattern.append(row)

		else:

			pattern.append(row)

		if index == len(data) - 1:
			if pattern[0][1] == "ORD":

				ord_rules.append(pattern)

			else:
				fixed = True

				for line in pattern:
					if int(line[4]) == 0:

						fixed = False
						break

				if fixed:

					fixed_start_occ_rules.append(pattern)

				else:

					unfixed_start_occ_rules.append(pattern)


		elif row_index != int(data[index + 1][0]):
			if pattern[0][1] == "ORD":

				ord_rules.append(pattern)

			else:
				fixed = True

				for line in pattern:
					if int(line[4]) == 0:

						fixed = False
						break

				if fixed:

					fixed_start_occ_rules.append(pattern)

				else:

					unfixed_start_occ_rules.append(pattern)
						
		index += 1

	return ord_rules, fixed_start_occ_rules, unfixed_start_occ_rules


def ord_rules_check(rules, data, window_size):

	ord_rules_results = []

	for rule in rules:

		precondition = (rule[0], rule[1][0])
		activation_counter = 0
		failures = []

		for row in data:

			found = False
			is_empty = False
			pattern_id = 0
			pattern_index = 0
			id_index = 0

			if rule[1][0][5] == "R=R":

				id_index = 2

			if row[6] == precondition[0][2] and row[7] == precondition[0][3]:
				for line in data:
					if int(line[4]) > int(row[4]):
						if not found and int(line[4]) <= int(row[4]) + window_size:
							if line[6] == precondition[1][2] and line[7] == precondition[1][3]:

								found = True
								activation_counter += 1
								pattern_index += 1

								if len(line[id_index]) == 0:

									is_empty = True
									failures.append(row)
									break

								else:

									pattern_id = int(line[id_index])

						elif found:
							if pattern_index == len(rule[1]):

								break

							if len(line[id_index]) != 0:
								if int(line[id_index]) == pattern_id:
									if line[6] == rule[1][pattern_index][2] and line[7] == rule[1][pattern_index][3]:

										pattern_index += 1

				if pattern_index != len(rule[1]) and not is_empty and found:

					failures.append(row)

		ord_rules_results.append((rule, activation_counter, failures))

	return ord_rules_results


def fixed_start_occ_rules_check(rules, data, window_size):

	fixed_start_occ_rules_results = []

	for rule in rules:

		precondition = (rule[0], rule[1][0])
		activation_counter = 0
		failures = []

		for row in data:

			is_empty = False
			pattern_id = 0
			id_index = 0
			check = []

			for i in range(0, len(rule[1])):

				check.append(False)

			if rule[1][0][5] == "R=R":

				id_index = 2
				
			if row[6] == precondition[0][2] and row[7] == precondition[0][3]:
				for line in data:
					if int(line[4]) > int(row[4]):
						if not check[0] and int(line[4]) <= int(row[4]) + window_size:
							if line[6] == precondition[1][2] and line[7] == precondition[1][3]:

								check[0] = True
								activation_counter += 1

								if len(line[id_index]) == 0:

									is_empty = True
									failures.append(row)
									break

								else:

									pattern_id = int(line[id_index])

						elif check[0]:
							if len(line[id_index]) != 0:
								if int(line[id_index]) == pattern_id:
									for i in range(1, len(rule[1])):
										if not check[i - 1]:
											if rule[1][i][2] == line[6] and rule[1][i][3] == line[7]:

												check[i - 1] = True
												break

				cnt = 0

				for item in check:
					if item:

						cnt += 1

				if not is_empty and check[0] and cnt != len(rule[1]) - 1:

					failures.append(row)

		fixed_start_occ_rules_results.append((rule, activation_counter, failures))

	return fixed_start_occ_rules_results


def unfixed_start_occ_rules_check(rules, data, window_size):

	unfixed_start_occ_rules_results = []

	for rule in rules:

		precondition = (rule[0], rule[1][0])
		activation_counter = 0
		failures = []
		id_index = 0

		first_lines = []
		symbolic_line = []

		for element in rule[1]:
			if int(element[4]) != -1:

				first_lines.append(element)

			if int(element[4]) == 1:

				symbolic_line = element

		if precondition[1][5] == "R=R":

			id_index = 2

		for row in data:

			pattern_ids = []
			patterns = []

			if row[6] == precondition[0][2] and row[7] == precondition[0][3]:

				for line in data:
					if int(line[4]) > int(row[4]) and int(line[4]) <= int(row[4]) + window_size:
						if len(line[id_index]) != 0:
							if int(line[id_index]) not in pattern_ids:
								for first_line in first_lines:
									if first_line[2] == line[6] and first_line[3] == line[7]:

										pattern_ids.append(int(line[id_index]))
										break

				for pattern_id in pattern_ids:

					pattern = []

					for line in data:
						if len(line[id_index]) != 0:
							if int(line[id_index]) == pattern_id:

								pattern.append(line)

					patterns.append(pattern)

				for pattern in patterns:

					valid = True

					for element in pattern:
						if int(element[4]) < int(row[4]):

							valid = False
							break

					if valid:

						found = False

						for element in pattern:
							if element[6] == symbolic_line[2] and element[7] == symbolic_line[3]:

								activation_counter += 1
								found = True
								break

						if found:

							rule_check = []
							pattern_check = []

							for element in rule[1]:

								rule_check.append(False)

							for element in pattern:

								pattern_check.append(False)

							for i in range(0, len(rule[1])):
								for j in range(0, len(pattern)):
									if rule[1][i][2] == pattern[j][6] and rule[1][i][3] == pattern[j][7] and not rule_check[i] and not pattern_check[j]:

										rule_check[i] = True
										pattern_check[j] = True

							cnt = 0

							for item in rule_check:
								if item:

									cnt += 1

							if cnt != len(rule[1]):

								failures.append(row)

		unfixed_start_occ_rules_results.append((rule, activation_counter, failures))

	return unfixed_start_occ_rules_results


def rep_rules_check(rules, data, pattern_window_size):

	rep_rules_results = []

	for rule in rules:

		pattern_ids = []
		counters = []
		id_index = 0
		starter_lines = []
		failures = []
		timestamps = []
		current_lines = []

		if rule[4] == "R=R":

			id_index = 2

		for row in data:
			if len(row[id_index]) != 0:
				if row[6] == rule[0] and row[7] == rule[1]:
					if int(row[id_index]) in pattern_ids:
						for i in range(0, len(pattern_ids)):
							if pattern_ids[i] == int(row[id_index]):

								counters[i] += 1
								current_lines[i] = row

					else:

						pattern_ids.append(int(row[id_index]))
						counters.append(1)
						starter_lines.append(row)
						current_lines.append(row)

		for i in range(0, len(pattern_ids)):
			if counters[i] < int(rule[2]) or counters[i] > int(rule[3]):

				failures.append(starter_lines[i])
				timestamps.append(int(current_lines[i][4]) + pattern_window_size)

		rep_rules_results.append((rule, len(pattern_ids), failures, timestamps))


	return rep_rules_results


def ord_RPC_rules_check(rules, data, pattern_window_size):

	ord_RPC_rules_results = []

	for rule in rules:

		precondition = rule[0]
		activation_counter = 0
		failures = []
		timestamps = []

		for line in data:

			is_empty = False
			pattern_id = 0
			pattern_index = 0
			id_index = 0
			found = False
			current_line = line

			if precondition[5] == "R=R":

				id_index = 2

			if line[6] == precondition[2] and line[7] == precondition[3]:

				activation_counter += 1
				found = True
				pattern_index += 1

				if len(line[id_index]) == 0:

					is_empty = True
					failures.append(line)
					timestamps.append(int(current_line[4]) + pattern_window_size)

				else:

					pattern_id = int(line[id_index])

					for row in data:
						if int(line[4]) < int(row[4]):
							if pattern_index == len(rule):

								break

							if len(row[id_index]) != 0:
								if int(row[id_index]) == pattern_id:
									if row[6] == rule[pattern_index][2] and row[7] == rule[pattern_index][3]:

										current_line = row
										pattern_index += 1

			if pattern_index != len(rule) and not is_empty and found:

				failures.append(line)
				timestamps.append(int(current_line[4]) + pattern_window_size)

		ord_RPC_rules_results.append((rule, activation_counter, failures, timestamps))


	return ord_RPC_rules_results


def fixed_start_occ_RPC_rules_check(rules, data, pattern_window_size):

	fixed_start_occ_RPC_rules_results = []

	for rule in rules:

		precondition = rule[0]
		activation_counter = 0
		failures = []
		timestamps = []

		for line in data:

			is_empty = False
			pattern_id = 0
			id_index = 0
			current_line = line

			if precondition[5] == "R=R":

				id_index = 2

			check = []

			for element in rule:

				check.append(False)

			if line[6] == precondition[2] and line[7] == precondition[3]:

				activation_counter += 1
				check[0] = True

				if len(line[id_index]) == 0:

					is_empty = True
					failures.append(line)
					timestamps.append(int(current_line[4]) + pattern_window_size)

				else:

					pattern_id = int(line[id_index])

					for row in data:
						if int(line[4]) < int(row[4]):

							cnt = 0

							for item in check:
								if item:

									cnt += 1

							if cnt == len(rule):

								break

							if len(row[id_index]) != 0:
								if int(row[id_index]) == pattern_id:
									for i in range(0, len(rule)):
										if row[6] == rule[i][2] and row[7] == rule[i][3] and not check[i]:

											check[i] = True
											current_line = row
											break

			cnt = 0

			for item in check:
				if item:

					cnt += 1

			if cnt != len(rule) and not is_empty and check[0]:

				failures.append(line)
				timestamps.append(int(current_line[4]) + pattern_window_size)

		fixed_start_occ_RPC_rules_results.append((rule, activation_counter, failures, timestamps))

	return fixed_start_occ_RPC_rules_results


def unfixed_start_occ_RPC_rules_check(rules, data, pattern_window_size):

	unfixed_start_occ_RPC_rules_results = []

	for rule in rules:

		activation_counter = 0
		failures = []
		timestamps = []
		id_index = 0

		if rule[0][5] == "R=R":

			id_index = 2

		first_lines = []
		symbolic_line = -1

		for i in range(0, len(rule)):
			if int(rule[i][4]) != -1:

				first_lines.append(i)

			if int(rule[i][4]) == 1:

				symbolic_line = i

		pattern_ids = []

		for line in data:
			for first_line in first_lines:

				current_line = line

				check = []
				found = False

				for element in rule:

					check.append(False)

				if line[6] == rule[first_line][2] and line[7] == rule[first_line][3]:
					
					check[first_line] = True

					if first_line == symbolic_line:
						
						found = True

						if len(line[id_index]) == 0:

							activation_counter += 1
							failures.append(line)
							timestamps.append(int(current_line[4]) + pattern_window_size)
							break

						elif int(line[id_index]) not in pattern_ids:

							activation_counter += 1

					if len(line[id_index]) == 0:

						break

					else:
						if int(line[id_index]) not in pattern_ids:

							pattern_ids.append(int(line[id_index]))

							for row in data:
								if int(row[4]) > int(line[4]):
									if len(row[id_index]) != 0:
										if int(row[id_index]) == int(line[id_index]):
											for i in range(0, len(rule)):
												if rule[i][2] == row[6] and rule[i][3] == row[7] and not check[i]:

													check[i] = True
													current_line = row

													if not found and i == symbolic_line:

														activation_counter += 1
														found = True

							cnt = 0

							for item in check:
								if item:

									cnt += 1

							if cnt != len(rule) and found:

								failures.append(line)
								timestamps.append(int(current_line[4]) + pattern_window_size)

		unfixed_start_occ_RPC_rules_results.append((rule, activation_counter, failures, timestamps))


	return unfixed_start_occ_RPC_rules_results


def REST_failures_check(data):

	REST_failures_5xx = []
	REST_failures_None = []
	REST_failures_Timeout = []
	REST_failures_4xx = []
	REST_failures_RPC = []

	for row in data:

		if row[12].startswith("5") and (row[7] == "GET" or row[7] == "PUT" or row[7] == "POST" or row[7] == "DELETE"):

			REST_failures_5xx.append(row)

		elif row[12] == "None":

			REST_failures_None.append(row)

		elif row[12] == "Timeout":

			REST_failures_Timeout.append(row)

		elif row[12].startswith("4") and (row[7] == "PUT" or row[7] == "POST" or row[7] == "DELETE"):

			REST_failures_4xx.append(row)

		elif (row[12].startswith("4") or row[12].startswith("5")) and len(row[10]) != 0:

			REST_failures_RPC.append(row)

	return REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC



def print_results(results, file):

	for result in results:

		file.write("REST: TARGET = " + result[0][0][2] + ", METHOD = " + result[0][0][3] + "\n\n")

		for element in result[0][1]:

			file.write("\tTARGET = " + element[2] + ", METHOD = " + element[3] + "\n")

		file.write("\nTIMES ACTIVATED: " + str(result[1]) + "\n")
		file.write("TIMES FAILED: " + str(len(result[2])) + "\n")

		if len(result[2]) != 0:

			file.write("\nFAILURES:\n\n")

		index = 0

		for element in result[2]:

			index += 1
			file.write(str(index) + ".\tTIMESTAMP = " + element[4] + ", REST STATUS CODE = " + element[12] + "\n")

		file.write("\n__________________________________________________________________________________________________________________________________________\n\n\n")


def print_failures(failures, file):


	if len(failures) == 0:

		file.write("No such REST failures\n")

	index = 0

	for failure in failures:

		index += 1
		method = failure[7]

		if method == "":

			method == "None"

		file.write(str(index) + ". \tTIMESTAMP = " + failure[4] + ", TARGET = " + failure[6] + ", METHOD = " + method + ", STATUS CODE = " + failure[12] + "\n")

	file.write("\n\n")


def print_RPC_results(results, file):

	for result in results:

		for element in result[0]:

			file.write("TARGET = " + element[2] + ", METHOD = " + element[3] + "\n")

		file.write("\nTIMES ACTIVATED: " + str(result[1]) + "\n")
		file.write("TIMES FAILED: " + str(len(result[2])) + "\n")

		if len(result[2]) != 0:

			file.write("\nFAILURES:\n\n")

		index = 0

		for element in result[3]:

			index += 1
			file.write(str(index) + ".\tTIMESTAMP = " + str(element) + "\n")

		file.write("\n__________________________________________________________________________________________________________________________________________\n\n\n")


def write_file(dest_path, ord_rules_results, fixed_start_occ_rules_results, unfixed_start_occ_rules_results, rep_rules_results, \
	ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
	REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC):

	if not dest_path.endswith('/'):

		dest_path = dest_path + "/"

	filename = dest_path + get_filename()
	file = open(filename, 'w', encoding = 'utf-8')
	#file.write("WINDOW SIZE: " + str(window_size) + "\n\n")
	#file.write("****************************************************************** ORDER RULES ******************************************************************\n\n\n")

	#print_results(ord_rules_results, file)

	#file.write("\n********************************************************* FIXED-START OCCURRANCE RULES *********************************************************\n\n\n")

	#print_results(fixed_start_occ_rules_results, file)

	#file.write("\n******************************************************** UNFIXED-START OCCURRANCE RULES ********************************************************\n\n\n")

	#print_results(unfixed_start_occ_rules_results, file)

	file.write("\n*************************************************************** REPETITION RULES ***************************************************************\n\n\n")

	for result in rep_rules_results:

		file.write("RULE: TARGET = " + result[0][0] + ", METHOD = " + result[0][1] + ", MINIMUM = " + result[0][2] + ", MAXIMUM = " + result[0][3] + "\n\n")

		file.write("TIMES ACTIVATED: " + str(result[1]) + "\n")
		file.write("TIMES FAILED: " + str(len(result[2])) + "\n")

		if len(result[2]) != 0:

			file.write("\nFAILURES:\n\n")

		index = 0

		for element in result[3]:

			index += 1
			file.write(str(index) + ".\tTIMESTAMP = " + str(element) + "\n")

		file.write("\n__________________________________________________________________________________________________________________________________________\n\n\n")

	file.write("**************************************************************** RPC ORDER RULES ****************************************************************\n\n\n")

	print_RPC_results(ord_RPC_rules_results, file)

	file.write("\n******************************************************* RPC FIXED-START OCCURRANCE RULES *******************************************************\n\n\n")

	print_RPC_results(fixed_start_occ_RPC_rules_results, file)

	file.write("\n****************************************************** RPC UNFIXED-START OCCURRANCE RULES ******************************************************\n\n\n")

	print_RPC_results(unfixed_start_occ_RPC_rules_results, file)

	file.write("\n************************************************************** REST FAILURES 5XX **************************************************************\n\n\n")

	print_failures(REST_failures_5xx, file)

	file.write("\n************************************************************** REST FAILURES NONE **************************************************************\n\n\n")

	print_failures(REST_failures_None, file)

	file.write("\n************************************************************ REST FAILURES TIMEOUT ************************************************************\n\n\n")

	print_failures(REST_failures_Timeout, file)

	file.write("\n************************************************************** REST FAILURES 4XX **************************************************************\n\n\n")

	print_failures(REST_failures_4xx, file)

	file.write("\n************************************************************** REST FAILURES RPC **************************************************************\n\n\n")

	print_failures(REST_failures_RPC, file)

	file.write("\n***********************************************************************************************************************************************")
	file.write("\n************************************************************* OPENSTACK ERROR LOG *************************************************************")
	file.write("\n***********************************************************************************************************************************************\n\n\n")

	bz_path = dest_path + "../../foreground_wl/"
	lines = []


	for bzip in os.listdir(bz_path):
		if "err" in bzip:
	
			bz_file = bz2.open(bz_path + bzip, mode = 'rt', encoding = 'utf-8')
	
			for line in bz_file:

				words = line.split()
				date = words[0] + " " + words[1]
				timestamp = (datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f") + datetime.timedelta(hours = 6)).timestamp()
				lines.append((timestamp, line))

	lines.sort(key=lambda x:x[0])

	for line in lines:

		file.write(line[1])

	file.close()

def write_total_report_instance(file, dest_path, rep_rules_results, \
			ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
			REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC):

	results = []

	for result in rep_rules_results:
		if len(result[2]) > 0:

			results.append(result)

	if len(results) > 0:

		file.write("\n*************************************************************** REPETITION RULES ***************************************************************\n\n\n")

	for result in results:

		file.write("RULE: TARGET = " + result[0][0] + ", METHOD = " + result[0][1] + ", MINIMUM = " + result[0][2] + ", MAXIMUM = " + result[0][3] + "\n\n")

		file.write("TIMES ACTIVATED: " + str(result[1]) + "\n")
		file.write("TIMES FAILED: " + str(len(result[2])) + "\n")

		if len(result[2]) != 0:

			file.write("\nFAILURES:\n\n")

		index = 0

		for element in result[3]:

			index += 1
			file.write(str(index) + ".\tTIMESTAMP = " + str(element) + "\n")

		file.write("\n__________________________________________________________________________________________________________________________________________\n\n\n")

	results = []

	for result in ord_RPC_rules_results:
		if len(result[2]) > 0:

			results.append(result)

	if len(results) > 0:

		file.write("**************************************************************** RPC ORDER RULES ****************************************************************\n\n\n")

		print_RPC_results(results, file)

	results = []

	for result in fixed_start_occ_RPC_rules_results:
		if len(result[2]) > 0:

			results.append(result)

	if len(results) > 0:

		file.write("\n******************************************************* RPC FIXED-START OCCURRANCE RULES *******************************************************\n\n\n")

		print_RPC_results(results, file)

	results = []

	for result in unfixed_start_occ_RPC_rules_results:
		if len(result[2]) > 0:

			results.append(result)

	if len(results) > 0:

		file.write("\n****************************************************** RPC UNFIXED-START OCCURRANCE RULES ******************************************************\n\n\n")

		print_RPC_results(results, file)

	if len(REST_failures_5xx) > 0:

		file.write("\n************************************************************** REST FAILURES 5XX **************************************************************\n\n\n")

		print_failures(REST_failures_5xx, file)

	if len(REST_failures_None) > 0:

		file.write("\n************************************************************** REST FAILURES NONE **************************************************************\n\n\n")

		print_failures(REST_failures_None, file)

	if len(REST_failures_Timeout) > 0:

		file.write("\n************************************************************ REST FAILURES TIMEOUT ************************************************************\n\n\n")

		print_failures(REST_failures_Timeout, file)

	if len(REST_failures_4xx) > 0:

		file.write("\n************************************************************** REST FAILURES 4XX **************************************************************\n\n\n")

		print_failures(REST_failures_4xx, file)

	if len(REST_failures_RPC) > 0:

		file.write("\n************************************************************** REST FAILURES RPC **************************************************************\n\n\n")

		print_failures(REST_failures_RPC, file)

	file.write("\n***********************************************************************************************************************************************")
	file.write("\n************************************************************* OPENSTACK ERROR LOG *************************************************************")
	file.write("\n***********************************************************************************************************************************************\n\n\n")

	bz_path = dest_path + "../../foreground_wl/"
	lines = []

	for bzip in os.listdir(bz_path):
		if "err" in bzip:
	
			bz_file = bz2.open(bz_path + bzip, mode = 'rt', encoding = 'utf-8')
	
			for line in bz_file:

				words = line.split()
				date = words[0] + " " + words[1]
				timestamp = (datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f") + datetime.timedelta(hours = 6)).timestamp()
				lines.append((timestamp, line))

	lines.sort(key=lambda x:x[0])

	for line in lines:

		file.write(line[1])

	file.close()



def write_total_report(dest_path, dest_total_report_path, rep_rules_results, \
	ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
	REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC):
	
	if not dest_total_report_path.endswith('/'):

		dest_total_report_path = dest_total_report_path + "/"

	if not dest_path.endswith('/'):

		dest_path = dest_path + "/"

	if os.path.isfile(dest_total_report_path + "total_report.txt"):

		file = open(dest_total_report_path + "total_report.txt", 'a', encoding = 'utf-8')
		file.write("\n\n\n\n======================================================================================================================================================\n")
		file.write("======================================================================================================================================================\n")
		file.write("======================================================================================================================================================\n")
		file.write("======================================================================================================================================================\n")
		file.write("======================================================================================================================================================\n\n\n\n\n")
		file.write(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(dest_path)))))) + "\n\n")

		write_total_report_instance(file, dest_path, rep_rules_results, \
			ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
			REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC)

	else:

		file = open(dest_total_report_path + "total_report.txt", 'w', encoding = 'utf-8')
		file.write(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(dest_path)))))) + "\n\n")

		write_total_report_instance(file, dest_path, rep_rules_results, \
			ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
			REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC)

	file.close()


def write_delta_timestamp(dest_path, dest_total_report_path, first_timestamp_log, \
	rep_rules_results, ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
	REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC):

	if not dest_total_report_path.endswith('/'):

		dest_total_report_path = dest_total_report_path + "/"

	if not dest_path.endswith('/'):

		dest_path = dest_path + "/"

	if os.path.isfile(dest_total_report_path + "delta_timestamp.csv"):

		file = open(dest_total_report_path + "delta_timestamp.csv", 'a', encoding = 'utf-8')

	else:

		file = open(dest_total_report_path + "delta_timestamp.csv", 'w', encoding = 'utf-8')

	file.write(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(dest_path)))))) + ";")

	timestamps = []

	for result in rep_rules_results:
		if len(result[3]) > 0:
			for timestamp in result[3]:

				timestamps.append(timestamp)

	for result in ord_RPC_rules_results:
		if len(result[3]) > 0:
			for timestamp in result[3]:

				timestamps.append(timestamp)

	for result in fixed_start_occ_RPC_rules_results:
		if len(result[3]) > 0:
			for timestamp in result[3]:

				timestamps.append(timestamp)

	for result in unfixed_start_occ_RPC_rules_results:
		if len(result[3]) > 0:
			for timestamp in result[3]:

				timestamps.append(timestamp)

	if len(REST_failures_5xx) > 0:
		for failure in REST_failures_5xx:

			timestamps.append(int(failure[4]) + int(failure[5]))

	if len(REST_failures_4xx) > 0:
		for failure in REST_failures_4xx:

			timestamps.append(int(failure[4]) + int(failure[5]))

	if len(REST_failures_RPC) > 0:
		for failure in REST_failures_RPC:

			timestamps.append(int(failure[4]) + int(failure[5]))

	if len(REST_failures_None) > 0:
		for failure in REST_failures_None:

			timestamps.append(int(failure[4]) + int(failure[5]))

	if len(REST_failures_Timeout) > 0:
		for failure in REST_failures_Timeout:

			timestamps.append(int(failure[4]) + int(failure[5]))

	first_timestamp = 0

	if len(timestamps) > 0:

		first_timestamp = min(timestamps) / 1000000

	first_error_openstack = 0

	bz_path = dest_path + "../../foreground_wl/"
	lines = []

	for bzip in os.listdir(bz_path):
		if "err" in bzip:
	
			bz_file = bz2.open(bz_path + bzip, mode = 'rt', encoding = 'utf-8')
	
			for line in bz_file:

				words = line.split()
				date = words[0] + " " + words[1]
				timestamp = (datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f") + datetime.timedelta(hours = 6)).timestamp()
				lines.append((timestamp, line))

	lines.sort(key=lambda x:x[0])

	for line in lines:
		if "Assertion results" not in line[1]:

			first_error_openstack = line[0]
			break

	ADS_delta = 0
	OS_delta = 0

	if first_timestamp != 0:

		ADS_delta = first_timestamp - first_timestamp_log

	if first_error_openstack != 0:

		OS_delta = first_error_openstack - first_timestamp_log


	if ADS_delta == 0 and OS_delta == 0:

		file.write("OpenStack found no failures;AD System found no failures\n")

	elif ADS_delta != 0 and OS_delta == 0:

		file.write("OpenStack found no failures;" + str(ADS_delta).replace(".", ",") + "\n")

	elif ADS_delta == 0 and OS_delta != 0:

		file.write(str(OS_delta).replace(".", ",") + ";AD System found no failures\n")

	else:
		
		file.write(str(OS_delta).replace(".", ",") + ";" + str(ADS_delta).replace(".", ",") + "\n")

	file.close()




def process_file(dest_path, src_log_path, src_rules_path, src_rep_path, src_RPC_path, window_size, dest_total_report_path, pattern_window_size):

	data = read_file(src_log_path)
	ord_rules, fixed_start_occ_rules, unfixed_start_occ_rules = read_rules(src_rules_path)
	rep_rules = read_rep_rules(src_rep_path)
	ord_RPC_rules, fixed_start_occ_RPC_rules, unfixed_start_occ_RPC_rules = read_RPC_rules(src_RPC_path)

	ord_rules_results = ord_rules_check(ord_rules, data, window_size)
	fixed_start_occ_rules_results = fixed_start_occ_rules_check(fixed_start_occ_rules, data, window_size)
	unfixed_start_occ_rules_results = unfixed_start_occ_rules_check(unfixed_start_occ_rules, data, window_size)
	rep_rules_results = rep_rules_check(rep_rules, data, pattern_window_size)
	ord_RPC_rules_results = ord_RPC_rules_check(ord_RPC_rules, data, pattern_window_size)
	fixed_start_occ_RPC_rules_results = fixed_start_occ_RPC_rules_check(fixed_start_occ_RPC_rules, data, pattern_window_size)
	unfixed_start_occ_RPC_rules_results = unfixed_start_occ_RPC_rules_check(unfixed_start_occ_RPC_rules, data, pattern_window_size)
	REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC = REST_failures_check(data)


	write_file(dest_path, ord_rules_results, fixed_start_occ_rules_results, unfixed_start_occ_rules_results, \
		rep_rules_results, ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
		REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC)

	write_total_report(dest_path, dest_total_report_path, \
		rep_rules_results, ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
		REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC)

	write_delta_timestamp(dest_path, dest_total_report_path, int(data[0][4]) / 1000000, \
		rep_rules_results, ord_RPC_rules_results, fixed_start_occ_RPC_rules_results, unfixed_start_occ_RPC_rules_results, \
		REST_failures_5xx, REST_failures_None, REST_failures_Timeout, REST_failures_4xx, REST_failures_RPC)





dest_path = sys.argv[1]
src_log_path = sys.argv[2]
src_rules_path = sys.argv[3]
src_rep_path = sys.argv[4]
src_RPC_path = sys.argv[5]
window_size = int(sys.argv[6])
dest_total_report_path = sys.argv[7]
pattern_window_size = int(sys.argv[8])

dest_path = create_folder(dest_path)

if os.path.isfile(src_log_path):

	process_file(dest_path, src_log_path, src_rules_path, src_rep_path, src_RPC_path, window_size, dest_total_report_path, pattern_window_size)

else:

	print("No such File")