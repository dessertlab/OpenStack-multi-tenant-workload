# This program needs as inputs (i) the path where you want to locate the destination folder (without the name of the destination folder)
# and (ii) the path of the file or the folder containing all and only the files (.log) you want to compute.
# The output will be a folder at the specified path containing all the .csv files generated.

import json
import sys
import os
import ast
import pdb

# Function for the creation the destination folder. Input: destination path. Return value: none.
def create_folder(path):
	if not path.endswith('/'):
		path = path + "/"

	path = path + "columns_selection"

	try:
	    os.mkdir(path)
	except OSError:
	    print ("Creation of the directory %s failed" % path)
	else:
	    print ("Successfully created the directory %s " % path)
	    return path

# Function for the generation of the header of the file. Input: file path. Return value: none. 
def add_header_temp(filename, header):
	file = open(filename, 'w', encoding = 'utf-8')
	for item in header:
		file.write(item + ";")
	file.write("\n")
	file.close()

# Function for the recognition of RPC error lines. Input: line to be evaluated. Return value: boolean value (True if is an error line)
def is_RPC_error_line(line):
	if line[0]["binaryAnnotations"][2]["key"] == "error":
		return True
	else:
		return False

# Function for the recognition of RPC lines. Input: line to be evaluated. Return value: boolean value (True if is a RPC line)
def is_RPC_line(line):
	if line[0]["binaryAnnotations"][0]["key"] == "caller_1:":
		return True
	else:
		return False

# Function for appending the RPC error line to the file. Input: line to be written, destination path. Return value: none.
def analyze_RPC_error_line(line, filename):

	body = line[0]["binaryAnnotations"][3]["value"].replace("set([", "([")
	body = ast.literal_eval(body)

	d = {}

	for key in body:
		if isinstance(body[key], dict):
			analyze_dict(body[key], key, d)
		elif not isinstance(body[key], list):
			if body[key] == "":
				d[key] = "None"
			else:
				d[key] = str(body[key]).replace("\n", "")

	return d

# Function for appending the RPC line to the file. Input: line to be written, destination path. Return value: none.
def analyze_RPC_line(line, filename):

	body = line[0]["binaryAnnotations"][2]["value"].replace("set([", "([")
	body = ast.literal_eval(body)

	d = {}

	for key in body:
		if isinstance(body[key], dict):
			analyze_dict(body[key], key, d)
		elif not isinstance(body[key], list):
			if body[key] == "":
				d[key] = "None"
			else:
				d[key] = str(body[key]).replace("\n", "")
	
	return d

def analyze_dict(body, super_key, super_dict):

	for key in body:

		new_key = super_key + "." + key

		if isinstance(body[key], dict):
			analyze_dict(body[key], new_key, super_dict)
		elif not isinstance(body[key], list):
			if body[key] == "":
				super_dict[key] = "None"
			else: 
				super_dict[new_key] = str(body[key]).replace("\n", "")

def write_line_temp(row, header, filename):
	file = open(filename, 'a', encoding = 'utf-8')

	for item in header:
		if item in row:

			file.write(row[item] + ";")

		else:

			file.write("NULL;")

	file.write("\n")

	file.close()


def add_header(filename):
	file = open(filename, 'w', encoding = 'utf-8')
	file.write("column_name;not_null_count;not_null_perc;none_count;none_perc;not_null_none_count;not_null_none_perc;values_count;max_equals_count;average_equals_count\n")
	file.close()


def is_potentially_interesting(not_null_count, none_count, not_null_none_count, values_count, max_equals_count, average_equals_count, dict_list):

	if none_count == len(dict_list):

		return False

	if not_null_none_count / len(dict_list) <= 0.015:

		return False

	if values_count / len(dict_list) <= 0.003:

		return False

	if max_equals_count <= 5:

		return False

	if isinstance(average_equals_count, str):
		if average_equals_count == "N/D":

			return False

	else:
		if average_equals_count <= 2:

			return False

	return True


def passes_combined_filtering(not_null_count, none_count, not_null_none_count, values_count, max_equals_count, average_equals_count, dict_list):

	if not_null_none_count / values_count >= 10:

		return False

	if max_equals_count / not_null_none_count >= 0.4:

		return False

	return True


def write_line(filename_general, filename_filtered, filename_combined_filtering, keys, dict_list):

	for key in keys:

		not_null_count = 0
		none_count = 0
		not_null_none_count = 0


		values = {}

		for row in dict_list:
			if key in row:

				not_null_count += 1

				if row[key] == "None":

					none_count += 1

				else:

					not_null_none_count += 1

					if row[key] not in values:

						values[row[key]] = 1

					else:

						values[row[key]] += 1

		not_null_perc = not_null_count / len(dict_list)
		none_perc = none_count / len(dict_list)
		not_null_none_perc = not_null_none_count / len(dict_list)

		values_count = len(values)

		if values_count == 0:

			average_equals_count = "N/D"

		else:

			average_equals_count = not_null_none_count / values_count

		max_equals_count = 0

		for item in values:
			if values[item] > max_equals_count:

				max_equals_count = values[item]

		file = open(filename_general, 'a', encoding = 'utf-8')
		file.write(key + ";" + str(not_null_count) + ";" + str(not_null_perc).replace(".", ",") + ";" + str(none_count) + ";" + str(none_perc).replace(".", ",") + ";")
		file.write(str(not_null_none_count) + ";" + str(not_null_none_perc).replace(".", ",") + ";" + str(values_count) + ";" + str(max_equals_count) + ";" + str(average_equals_count).replace(".", ",") + "\n")
		file.close()

		if is_potentially_interesting(not_null_count, none_count, not_null_none_count, values_count, max_equals_count, average_equals_count, dict_list):

			file = open(filename_filtered, 'a', encoding = 'utf-8')
			file.write(key + ";" + str(not_null_count) + ";" + str(not_null_perc).replace(".", ",") + ";" + str(none_count) + ";" + str(none_perc).replace(".", ",") + ";")
			file.write(str(not_null_none_count) + ";" + str(not_null_none_perc).replace(".", ",") + ";" + str(values_count) + ";" + str(max_equals_count) + ";" + str(average_equals_count).replace(".", ",") + "\n")
			file.close()

			if passes_combined_filtering(not_null_count, none_count, not_null_none_count, values_count, max_equals_count, average_equals_count, dict_list):

				file = open(filename_combined_filtering, 'a', encoding = 'utf-8')
				file.write(key + ";" + str(not_null_count) + ";" + str(not_null_perc).replace(".", ",") + ";" + str(none_count) + ";" + str(none_perc).replace(".", ",") + ";")
				file.write(str(not_null_none_count) + ";" + str(not_null_none_perc).replace(".", ",") + ";" + str(values_count) + ";" + str(max_equals_count) + ";" + str(average_equals_count).replace(".", ",") + "\n")
				file.close()

# Function for processing the file and write the corresponding .csv file. 
# Input: source path of the file to be processed, destination path of the .csv file. Return value: none.
def process_file(read_path, path):
	file = open(read_path, 'r', encoding = 'utf-8')
	data = json.load(file)
	file.close()

	filename_general = path + "/columns_selection_general.csv"
	filename_filtered = path + "/columns_selection_filtered.csv"
	filename_combined_filtering = path + "/columns_selection_combined_filtering.csv"

	dict_list = []

	print(len(data))

	for line in data:
		if is_RPC_line(line):
			if is_RPC_error_line(line):
				dict_list.append(analyze_RPC_error_line(line, filename_general))
			else:
				dict_list.append(analyze_RPC_line(line, filename_general))

	print(len(dict_list))

	keys = []

	for row in dict_list:
		for key in row:
			if key not in keys:

				keys.append(key)

	add_header(filename_general)
	add_header(filename_filtered)
	add_header(filename_combined_filtering)

	write_line(filename_general, filename_filtered, filename_combined_filtering, keys, dict_list)

#
#	add_header_temp(filename, keys)
#
#	for row in dict_list:
#
#		write_line_temp(row, keys, filename)

	print("Successfully created the file: %s" % filename_filtered)


write_path = sys.argv[1]
write_path = create_folder(write_path)

read_path = sys.argv[2]
path = read_path

if os.path.isdir(read_path):
	if not read_path.endswith('/'):
		path = read_path + "/"

	for file in os.listdir(read_path):
		if file != ".DS_Store":
			process_file(path + file, write_path)
elif os.path.isfile(read_path):
	process_file(read_path, write_path)
else:
	print("No such File or Directory")