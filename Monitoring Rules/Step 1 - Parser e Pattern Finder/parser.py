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

	path = path + "csv"

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
	file.write("timestamp" + ";" + "duration" + ";" + "target" + ";" + "method" + ";" + "global_request_id" + ";" + "request_id" + ";" + "caller_1" + ";" + "caller_2" + ";" + "status_code" + "\n")
	file.close()

# Function for the recognition of RPC error lines. Input: line to be evaluated. Return value: boolean value (True if is an error line)
def is_RPC_error_line(line):
	if line[0]["binaryAnnotations"][2]["key"] == "error":
		return True
	else:
		return False

# Function for the recognition of REST error lines. Input: line to be evaluated. Return value: boolean value (True if is an error line)
def is_REST_error_line(line):
	if line[0]["binaryAnnotations"][0]["key"] == "error":
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
def write_RPC_error_line(line, filename):
	timestamp = str(line[0]["timestamp"])
	duration = str(line[0]["duration"])
	target = line[0]["binaryAnnotations"][5]["value"][8:(len(line[0]["binaryAnnotations"][5]["value"]) - 1)].replace(".localdomain", "")
	method = line[0]["binaryAnnotations"][4]["value"]

	body = line[0]["binaryAnnotations"][3]["value"].replace("set([", "([")
	body = ast.literal_eval(body)
	#breakpoint()
	if "_context_global_request_id" in body:
		request_id = body["_context_request_id"]
		if body["_context_global_request_id"] is None:
			global_request_id = "None"
		else: 
			global_request_id = str(body["_context_global_request_id"])
	else: 
		request_id = "None"
		global_request_id = "None"

	caller_1 = line[0]["binaryAnnotations"][0]["value"]
	caller_2 = line[0]["binaryAnnotations"][1]["value"]
	status_code = ""

	file = open(filename, 'a', encoding = 'utf-8')
	file.write(timestamp + ";" + duration + ";" + target + ";" + method + ";" + global_request_id + ";" + request_id + ";" + caller_1 + ";" + caller_2 + ";" + status_code + "\n")
	file.close()
	return

# Function for appending the RPC line to the file. Input: line to be written, destination path. Return value: none.
def write_RPC_line(line, filename):
	timestamp = str(line[0]["timestamp"])
	duration = str(line[0]["duration"])
	target = line[0]["binaryAnnotations"][4]["value"][8:(len(line[0]["binaryAnnotations"][4]["value"]) - 1)].replace(".localdomain", "")
	method = line[0]["binaryAnnotations"][3]["value"]

	body = line[0]["binaryAnnotations"][2]["value"].replace("set([", "([")
	body = ast.literal_eval(body)

	if body["_context_global_request_id"] is None:
		global_request_id = "None"
	else: 
		global_request_id = str(body["_context_global_request_id"])

	request_id = body["_context_request_id"]
	caller_1 = line[0]["binaryAnnotations"][0]["value"]
	caller_2 = line[0]["binaryAnnotations"][1]["value"]

	status_code = ""
	
	if "args" in body:
		if "objinst" in body["args"]:
			if "nova_object.data" in body["args"]["objinst"]:
				if "code" in body["args"]["objinst"]["nova_object.data"]:
					status_code = str(body["args"]["objinst"]["nova_object.data"]["code"])
			elif "neutron_object.data" in body["args"]["objinst"]:
				if "code" in body["args"]["objinst"]["neutron_object.data"]:
					breakpoint()
					status_code = str(body["args"]["objinst"]["neutron_object.data"]["code"])
			elif "cinder_object.data" in body["args"]["objinst"]:
				if "code" in body["args"]["objinst"]["cinder_object.data"]:
					breakpoint()
					status_code = str(body["args"]["objinst"]["cinder_object.data"]["code"])

	file = open(filename, 'a', encoding = 'utf-8')
	file.write(timestamp + ";" + duration + ";" + target + ";" + method + ";" + global_request_id + ";" + request_id + ";" + caller_1 + ";" + caller_2 + ";" + status_code + "\n")
	file.close()

# Function for appending the REST error line to the file. Input: line to be written, destination path. Return value: none.
def write_REST_error_line(line, filename):
	timestamp = str(line[0]["timestamp"])
	duration = str(line[0]["duration"])
	if len(line[0]["binaryAnnotations"]) == 1:
		method = ""
		status_code = "Timeout"
		target = line[0]["binaryAnnotations"][0]["endpoint"]["serviceName"].replace("sessionclient_request_", "")
	else:
		target = line[0]["binaryAnnotations"][2]["value"]
		method = line[0]["binaryAnnotations"][1]["value"]
		status_code = line[0]["binaryAnnotations"][0]["value"]
		words = status_code.split()
		status_code = words[words.index("(HTTP") + 1].replace(")", "")
	global_request_id = ""
	request_id = ""
	caller_1 = ""
	caller_2 = ""

	file = open(filename, 'a', encoding = 'utf-8')
	file.write(timestamp + ";" + duration + ";" + target + ";" + method + ";" + global_request_id + ";" + request_id + ";" + caller_1 + ";" + caller_2 + ";" + status_code + "\n")
	file.close()

# Function for appending the REST line to the file. Input: line to be written, destination path. Return value: none.
def write_REST_line(line, filename):
	timestamp = str(line[0]["timestamp"])
	duration = str(line[0]["duration"])
	if len(line[0]["binaryAnnotations"]) == 4:
		target = line[0]["binaryAnnotations"][3]["value"]
		method = line[0]["binaryAnnotations"][0]["value"]
		status_code = str(line[0]["binaryAnnotations"][2]["value"])
	elif len(line[0]["binaryAnnotations"]) == 2:
		target = line[0]["binaryAnnotations"][1]["value"]
		method = line[0]["binaryAnnotations"][0]["value"]
		status_code = "None"
	global_request_id = ""
	request_id = ""
	caller_1 = ""
	caller_2 = ""
	

	file = open(filename, 'a', encoding = 'utf-8')
	file.write(timestamp + ";" + duration + ";" + target + ";" + method + ";" + global_request_id + ";" + request_id + ";" + caller_1 + ";" + caller_2 + ";" + status_code + "\n")
	file.close()

# Function for processing the file and write the corresponding .csv file. 
# Input: source path of the file to be processed, destination path of the .csv file. Return value: none.
def process_file(read_path, path):
	file = open(read_path, 'r', encoding = 'utf-8')
	data = json.load(file)
	file.close()

	filename = path + "/" + get_filename(read_path)
	add_header(filename)

	for line in data:
		if is_RPC_line(line):
			if is_RPC_error_line(line):
				write_RPC_error_line(line, filename)
			else:
				write_RPC_line(line, filename)
		else:
			if is_REST_error_line(line):
				write_REST_error_line(line, filename)
			else:
				write_REST_line(line, filename)

	print("Successfully created the file: %s" % get_filename(read_path))




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