# This program needs as inputs (i) the path where you want to locate the destination folder (without the name of the destination folder),
# (ii) the path of the file or the folder containing all and only the files (.log) you want to compute, (iii) the value of the window size
# you want to use for this computation. The output will be a folder at the specified path containing all the .csv files generated.

import csv
import sys
import os

# Function for the creation the destination folder. Input: destination path, window size. Return value: none.
def create_folder(path, window_size):
	if not path.endswith('/'):
		path = path + "/"

	path = path + "csv_patterns_" + str(window_size)

	try:
	    os.mkdir(path)
	except OSError:
	    print ("Creation of the directory %s failed" % path)
	else:
	    print ("Successfully created the directory %s " % path)
	    return path

# Function for obtaining the filename without folder and extension. Input: path of the file. Return value: file name.
def get_filename(path):
	filename, extension = os.path.splitext(os.path.basename(path))
	filename = filename + ".csv"
	return filename

# Function for the generation of the header of the file. Input: file path. Return value: none. 
def add_header(filename):
	file = open(filename, 'w', encoding = 'utf-8')
	file.write("gr_id" + ";" + "gr_occs" + ";" + "rr_id" + ";" + "rr_occs" + ";" + "timestamp" + ";" + "duration" + ";" + "target" + ";" + "method" + ";" + "global_request_id" + ";" + "request_id" + ";" + "caller_1" + ";" + "caller_2" + ";" + "status_code" + "\n")
	file.close()

# Recursive function for the iteration in order to find patterns Global = Request. 
# Input: data read from the file, patterns list, starting index, window size, pattern id, request id, pattern elements counter, boolean value for pattern type. 
# Return value: patterns list modified, updated counter, boolean value for pattern type.
def search_pattern_gr(data, patterns, index, window_size, pattern_id, request_id, counter, found):
	row = data[index]

	for i in range(index + 1, len(data)):
		if int(row[0]) + window_size > int(data[i][0]):
			if (request_id == data[i][5] or request_id == data[i][4]) and patterns[i][0] is False:
				if request_id == data[i][4]:
					found = True

				counter = counter + 1

				patterns, counter, found = search_pattern_gr(data, patterns, i, window_size, pattern_id, request_id, counter, found)

				if found:
					patterns[i][1] = str(pattern_id + 1)
					patterns[i][2] = str(counter)
					patterns[i][0] = True

				break
		else:
			break

	return patterns, counter, found

# Recursive function for the iteration in order to find patterns Request = Request. 
# Input: data read from the file, patterns list, starting index, window size, pattern id, request id, pattern elements counter. 
# Return value: patterns list modified, updated counter.
def search_pattern_rr(data, patterns, index, window_size, pattern_id, request_id, counter):
	row = data[index]

	for i in range(index + 1, len(data)):
		if int(row[0]) + window_size > int(data[i][0]):
			if request_id == data[i][5] and patterns[i][0] is False:
				counter = counter + 1

				patterns, counter = search_pattern_rr(data, patterns, i, window_size, pattern_id, request_id, counter)

				patterns[i][0] = True
				patterns[i][1] = str(pattern_id)
				patterns[i][2] = str(counter)

				break
		else:
			break

	return patterns, counter

# Function for writing the .csv file produced. Input: file name, data read from the original file, patterns list. Return value: none. 
def write_csv_file(filename, data, patterns_gr, patterns_rr):
	add_header(filename)
	for i in range(0, len(data)):
		file = open(filename, 'a', encoding = 'utf-8')
		file.write(patterns_gr[i][1] + ";" + patterns_gr[i][2] + ";" + patterns_rr[i][1] + ";" + patterns_rr[i][2] + ";" + data[i][0] + ";" + data[i][1] + ";" + data[i][2] + ";" + data[i][3] + ";" + data[i][4] + ";" + data[i][5] + ";" + data[i][6] + ";" + data[i][7] + ";" + data[i][8] + "\n")
		file.close()

# Function for processing the file and write the corresponding .csv file. 
# Input: source path of the file to be processed, destination path of the .csv file, window size. Return value: none.
def process_file(read_path, path, window_size):
	file  = open(read_path, 'r', encoding = 'utf-8')
	reader = csv.reader(file, delimiter = ";")

	data = []
	patterns_gr = []
	patterns_rr = []

	index = 0
	for row in reader:
		if index != 0:
			data.append(row)
			pattern_rr = [False, "", ""]
			pattern_gr = [False, "", ""]
			patterns_rr.append(pattern_rr)
			patterns_gr.append(pattern_gr)
		
		index = index + 1

	file.close()
	data.reverse()
	pattern_id = 0
	index = 0

	for row in data:
		if patterns_gr[index][0] is False: 
			for i in range(index + 1, len(data)):
				if int(row[0]) + window_size > int(data[i][0]):
					if len(row[4]) != 0 and (row[5] == data[i][5] or row[5] == data[i][4]) and patterns_gr[i][0] is False and row[5] != "None":
						found = False

						if row[5] == data[i][4]:
							found = True

						patterns_gr, counter, found = search_pattern_gr(data, patterns_gr, i, window_size, pattern_id, row[5], 2, found)

						if found:
							pattern_id = pattern_id + 1

							patterns_gr[index][0] = True
							patterns_gr[index][1] = str(pattern_id)
							patterns_gr[index][2] = str(counter)

							patterns_gr[i][0] = True
							patterns_gr[i][1] = str(pattern_id)
							patterns_gr[i][2] = str(counter)

						break
				else:
					break

		index = index + 1
	
	pattern_id = 0
	index = 0

	for row in data:
		if patterns_rr[index][0] is False:
			for i in range(index + 1, len(data)):
				if int(row[0]) + window_size > int(data[i][0]):
					if len(row[4]) != 0 and row[5] == data[i][5] and patterns_rr[i][0] is False and row[5] != "None":
						pattern_id = pattern_id + 1
						patterns_rr, counter = search_pattern_rr(data, patterns_rr, i, window_size, pattern_id, row[5], 2)

						patterns_rr[index][0] = True
						patterns_rr[index][1] = str(pattern_id)
						patterns_rr[index][2] = str(counter)

						patterns_rr[i][0] = True
						patterns_rr[i][1] = str(pattern_id)
						patterns_rr[i][2] = str(counter)

						break
				else:
					break

		index = index + 1
	
	filename = path + "/" + get_filename(read_path)
	write_csv_file(filename, data, patterns_gr, patterns_rr)
	print("Successfully created the file %s" % get_filename(read_path))



write_path = sys.argv[1]
read_path = sys.argv[2]
window_size = int(sys.argv[3])

write_path = create_folder(write_path, window_size)
path = read_path



if os.path.isdir(read_path):
	if not read_path.endswith('/'):
		path = read_path + "/"

	for file in os.listdir(read_path):
		process_file(path + file, write_path, window_size)
elif os.path.isfile(read_path):
	process_file(read_path, write_path, window_size)
else:
	print("No such File or Directory")