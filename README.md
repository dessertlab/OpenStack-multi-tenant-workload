# OpenStack-multi-tenant-workload


This repository contains the logs collected during the execution of the OpenStack cloud computing platform with a multi-tenant workload. 

The workload simulates 10 different tenants performing concurrent operations on the cloud infrastructure.
The tenants exhibit 6 different profiles, as described in the following:

* *Volume*: The tenant performs operations strictly related to the block storage (Cinder subsystem);
 
* *Instance*: The tenant stresses the Nova subsystem for the creation of VM instances;
    
* *Network*: The tenant creates network resources (networks, sub-networks, IP addresses, routers, etc.), stressing the Neutron subsystem;
    
* *Instance Volume*: The tenant creates an instance from an image, then a storage volume;
    
* *Volume Instance*: The tenant creates a volume and then an instance starting from the volume;
    
* *DEPL (Deployment workload)*: The tenant stresses the Nova, Cinder, and Neutron subsystems in a balanced way. 
    
These six profiles are run concurrently to generate a multi-tenant workload. The *Volume Only*, *Network Only*, *Instance before Volume*, and *Volume before Instance* profiles are run twice by different tenants, as shown in the following figure.

![alt text](https://github.com/dessertlab/OpenStack-multi-tenant-workload/blob/main/img/workload.png?raw=true)



The execution of the workload lasts ~40 minutes and produces a large amount of data. On average, during every system execution, we collected 69 different event types (59 RPC and 10 REST API), and ~2,700 different events ~2,100 RPC events, while the remaining are related to the REST API calls). For every execution trace, the bodies of all RPC events contain in total more than ~155,000 fields (on average, 74 body fields per event).

## Fault-Injection

The folder "`Fault-Injection`" includes the raw logs from fault injection experiments in OpenStack. The tests are grouped per injected sub-system (i.e., Nova, Cinder, and Neutron). 

There is a total of 637 tests: 292 for Nova, 224 for Cinder, and 121 for Neutron. The logs of each experiment are saved in a folder named "`Test_id`", where "`id`" is an incremental number that identifies the test. 

Every test folder contains the following files:
* "`fp_info.data`": It contains information about the fault injected in the experiment (including the fault type, the target component, the target class, the target function, and the fault injection point);
* "`orig_file`": It contains the target component before the mutation;
* "`mutated_file`": It contains the target component after the mutation;

The subfolder "`Test_<id>/logs/round_1`" contains the raw logs of the executions of the fault-injection experiments.

In each round subfolder, there are more subfolders representing different sub-systems of OpenStack (e.g., "`nova`", "`cinder`", "`neutron`", "`glance`", etc.) containing the log messages generated during the tests.

For example, the directory "`Nova/Test_1/logs/round_1/cinder`" contains the log messages from the Cinder sub-system during the faulty execution of "Test 1", from the fault injection campaign on the Nova sub-system. 

Furthermore, for each round, there is the "`foreground_wl`" subfolder containing the log files of the workload:

* `openstack_demo_workload-<tenant_id>-timestamp.out.log.bzip2.out` (contains the log messages of the workload execution)

* `openstack_demo_workload-<tenant_id>-timestamp.err.log.bzip2.out` (contains the error messages during the workload execution, including both API Errors and Assertion Failures).

where <tenant_id> is a number between 0 and 9 representing one of the 10 different tenants.

Each subfolder "`Test_<id>/logs/round_number`" contains also the file "`trace_Test_<id>.log`". This file is a JSON file containing all the messages exchanged in OpenStack during the execution of the workload. These messages are collected with the distributed tracing system [Zipkin](https://zipkin.io/).


## Fault-Free

The folder "`Fault-Free`" includes the raw logs from 50 correct execution of the OpenStack cloud computing systems, i.e., when no fault is injected into the system.
