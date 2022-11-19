#!/bin/bash
cd "$(dirname "$0")"

################ START CONFIGURATION PARAMETERS ######################

#get timestamp
timestamp=$(date +"%s")
id=$1

##### CREATE ADMIN credential file according to env varibale set by PyCAST  #####

if [ -z "$PYCAST_ADMIN_NAME" ]; then
    PYCAST_ADMIN_NAME="admin"
fi

if [ -z "$PYCAST_ADMIN_PWD" ]; then
    PYCAST_ADMIN_PWD="admin"
fi

if [ -z "$PYCAST_ADMIN_PROJECT_NAME" ]; then
    PYCAST_ADMIN_PROJECT_NAME="admin"
fi

if [ -z "$PYCAST_ADMIN_DOMAIN_NAME" ]; then
    PYCAST_ADMIN_DOMAIN_NAME="Default"
fi

admin_keystonrc_file_name="admin_keystonrc_tempest-"${id}"-"${timestamp}

IFS='' read -r -d '' admin_keystonrc_file_content <<EOF
unset OS_SERVICE_TOKEN
export OS_USERNAME=${PYCAST_ADMIN_NAME}
export OS_PASSWORD='${PYCAST_ADMIN_PWD}'
export OS_AUTH_URL=http://localhost:5000/v3
export PS1='[\u@\h \W(keystone_${PYCAST_ADMIN_NAME})]\$ '
export OS_PROJECT_NAME=${PYCAST_ADMIN_PROJECT_NAME}
export OS_USER_DOMAIN_NAME=${PYCAST_ADMIN_DOMAIN_NAME}
export OS_PROJECT_DOMAIN_NAME=${PYCAST_ADMIN_DOMAIN_NAME}
export OS_IDENTITY_API_VERSION=3
EOF

echo "${admin_keystonrc_file_content}" > /tmp/${admin_keystonrc_file_name}

#KEYSTONE_ADMIN_FILE="keystonerc_admin"
#KEYSTONE_ADMIN_FILE_path="/root/"

#assume that admin credential are in /root dir
#source ${KEYSTONE_ADMIN_FILE_path}"/"${KEYSTONE_ADMIN_FILE}
source /tmp/${admin_keystonrc_file_name}

#out and err files
STD_ERR_FILE="/tmp/openstack_demo_workload-${id}"-"${timestamp}.err"
STD_OUT_FILE="/tmp/openstack_demo_workload-${id}"-"${timestamp}.out"

E_API_ERROR=98
trap "exit $E_API_ERROR" TERM
export TOP_PID=$$

tmp_stdout="/tmp/stdout_${id}"
tmp_stderr="/tmp/stderr_${id}"

# LAUNCH AND CHECK CONFIGURATION 
function launch_and_check_pipe(){
  E_API_ERROR=98
  echo "[START] ${@}" | ./predate.sh >> ${STD_OUT_FILE}
  $@ 1>${tmp_stdout} 2>${tmp_stderr}
  cat ${tmp_stdout} | tee >> ${STD_OUT_FILE} | echo "$(cat ${tmp_stdout})"
  cat ${tmp_stderr} | ./predate.sh >> ${STD_OUT_FILE}
  if [ $(cat ${tmp_stderr} | wc -l) -ne 0 ]; then
	cat ${tmp_stderr} | grep "deprecated" >/dev/null 2>&1
	if [ $? -ne 0 ]; then
	        echo "API ERROR: " ${@} ";" $(cat ${tmp_stderr}) | ./predate.sh >> ${STD_ERR_FILE}
		    #kill -s TERM $TOP_PID
        	#exit $E_API_ERROR
	fi
  fi
  echo "[END] ${@}" | ./predate.sh >> ${STD_OUT_FILE}
}

function launch_and_check(){
  E_API_ERROR=98
  echo "[START] ${@}" | ./predate.sh >> ${STD_OUT_FILE}
  $@ 1>${tmp_stdout} 2>${tmp_stderr}
  cat ${tmp_stdout} >> ${STD_OUT_FILE}
  cat ${tmp_stderr} | ./predate.sh >> ${STD_OUT_FILE}
  if [  $(cat ${tmp_stderr} | wc -l) -ne 0 ]; then
	cat ${tmp_stderr} | grep "deprecated" >/dev/null 2>&1
	if [ $? -ne 0 ]; then  		
        	echo "API ERROR: " ${@} ";" $(cat ${tmp_stderr}) | ./predate.sh >> ${STD_ERR_FILE}
        	#exit $E_API_ERROR
		    #kill -s TERM $TOP_PID
	fi
  fi
  echo "[END] ${@}" | ./predate.sh >> ${STD_OUT_FILE}
}

# Config parameters
IMAGE_NAME="tempest-cirros-0.4.0-x86_64-"${id}"-"${timestamp}
IMAGE_FILE="cirros-0.4.0-x86_64-disk.img"

KEY_NAME="tempest-pycast_keypair-"${id}"-"${timestamp}
SECURITY_GROUP_NAME="tempest-SECURITY_GROUP_SAMPLE-"${id}"-"${timestamp}

INSTANCE_NAME="tempest-INSTANCE_SAMPLE-"${id}"-"${timestamp}

VOLUME_NAME="tempest-VOLUME_SAMPLE-"${id}"-"${timestamp}
VOLUME_SIZE=1
AVAILABILITY_ZONE="nova"

#by default 'public' is the name of external network
PUBLIC_NETWORK_NAME="public"

PRIVATE_NETWORK_NAME="tempest-private-"${id}"-"${timestamp}

#create new domain, project, user, role about that workload
DOMAIN_NAME="tempest-domain-"${id}"-"${timestamp}
PROJECT_NAME="tempest-project-"${id}"-"${timestamp}
USER_NAME="tempest-user-"${id}"-"${timestamp}
USER_PWD=${USER_NAME}
ROLE_NAME="tempest-role-"${id}"-"${timestamp}

launch_and_check "openstack domain create ${DOMAIN_NAME}"
launch_and_check "openstack project create --domain ${DOMAIN_NAME} ${PROJECT_NAME}"
launch_and_check "openstack user create --domain ${DOMAIN_NAME} --password ${USER_PWD} ${USER_NAME}"
#launch_and_check "openstack role create ${ROLE_NAME}"
launch_and_check "openstack role add --project ${PROJECT_NAME} --user ${USER_NAME} admin"

#create keystonrc file to be used

keystonrc_file_name="keystonerc_tempest-"${id}"-"${timestamp}

IFS='' read -r -d '' keystonrc_file_content <<EOF
unset OS_SERVICE_TOKEN
export OS_USERNAME=${USER_NAME}
export OS_PASSWORD='${USER_PWD}'
export OS_AUTH_URL=http://localhost:5000/v3
export PS1='[\u@\h \W(keystone_${USER_NAME})]\$ '
export OS_PROJECT_NAME=${PROJECT_NAME}
export OS_USER_DOMAIN_NAME=${DOMAIN_NAME}
export OS_PROJECT_DOMAIN_NAME=${DOMAIN_NAME}
export OS_IDENTITY_API_VERSION=3
EOF

echo "${keystonrc_file_content}" > /tmp/${keystonrc_file_name}

source /tmp/${keystonrc_file_name}

subnet_prefix=$(launch_and_check_pipe "openstack subnet list" | grep "public" | sed 's/|//g' | awk -F " " '{print $4}' | awk -F "." '{print $1"."$2"."$3}')
FIP=${subnet_prefix}"."$(( $id + 100 ));
existent_subnet_ip=$(launch_and_check_pipe "openstack subnet list" |grep -v tempest |sed 's/|//g'|awk '$0 !~ "+" && NR>3{print $4}'|awk -F. '{print $1}'|while read ip; do echo -n $ip" "; done)
#echo "existent_subnet_ip ${existent_subnet_ip}"
array=($existent_subnet_ip)

#check if generate subnet already exists
ip_1_digit=10
for ip in ${!array[*]}; do
    cur_ip=${array[$ip]}
    #echo "cur_ip= $cur_ip"
    if [ $cur_ip -eq $ip_1_digit ]; then
            let "ip_1_digit=ip_1_digit+1"
    fi
done

ip_2_digit=$(perl -le '$,=".";print map int rand 253,1..1')

header_subnet=${ip_1_digit}"."${ip_2_digit}

PRIVATE_SUBNET_RANGE=${header_subnet}".1.0/24"
PRIVATE_SUBNET_NAME="tempest-private-subnet-"${id}"-"${timestamp}
PRIVATE_SUBNET_GATEWAY=${header_subnet}".1.1"

ROUTER_NAME="tempest-router-"${id}"-"${timestamp}


################ END CONFIGURATION PARAMETERS ######################

assert(){

    E_ASSERT_FAILED=99

    if [ -z "$1" ]; then
        return $E_PARAM_ERR   #  No damage done.
    fi
    
    if [ $1 -ne 0 ]; then

            if [ "$2" == "image_active" ]; then
                    echo_time "Assertion results: FAILURE_IMAGE_ACTIVE" >> ${STD_ERR_FILE}

            elif [ "$2" == "instance_active" ]; then
                    echo_time "Assertion results: FAILURE_INSTANCE_ACTIVE" >> ${STD_ERR_FILE}

            elif [ "$2" == "ssh" ]; then
                    echo_time "Assertion results: FAILURE_SSH" >> ${STD_ERR_FILE}

            elif [ "$2" == "keypair" ]; then
                    echo_time "Assertion results: FAILURE_KEYPAIR" >> ${STD_ERR_FILE}

            elif [ "$2" == "security_group" ]; then
                    echo_time "Assertion results: FAILURE_SECURITY_GROUP" >> ${STD_ERR_FILE}

            elif [ "$2" == "volume_created" ]; then
                    echo_time "Assertion results: FAILURE_VOLUME_CREATED" >> ${STD_ERR_FILE}

            elif [ "$2" == "volume_attached" ]; then
                    echo_time "Assertion results: FAILURE_VOLUME_ATTACHED" >> ${STD_ERR_FILE}

            elif [ "$2" == "floating_ip_created" ]; then
                    echo_time "Assertion results: FAILURE_FLOATING_IP_CREATED" >> ${STD_ERR_FILE}
	    
            elif [ "$2" == "net_active" ]; then
                    echo_time "Assertion results: FAILURE_PRIVATE_NETWORK_ACTIVE" >> ${STD_ERR_FILE}

            elif [ "$2" == "subnet_created" ]; then
                    echo_time "Assertion results: FAILURE_PRIVATE_SUBNET_CREATED" >> ${STD_ERR_FILE}

            elif [ "$2" == "router_active" ]; then
                    echo_time "Assertion results: FAILURE_ROUTER_ACTIVE" >> ${STD_ERR_FILE}

            elif [ "$2" == "router_interface_created" ]; then
                    echo_time "Assertion results: FAILURE_ROUTER_INTERFACE_CREATED" >> ${STD_ERR_FILE}

            elif [ "$2" == "floating_ip_added" ]; then
                    echo_time "Assertion results: FAILURE_FLOATING_IP_ADDED" >> ${STD_ERR_FILE}

            fi

            echo_time "Failure!!!" >> ${STD_OUT_FILE}
            echo "1"
            #exit $E_ASSERT_FAILED
    else
  
            echo "0"
    fi
}

echo_time() {
    date +"%Y-%m-%d %H:%M:%S.%6N INFO [sample_workload.sh]: $*"
}


check_image_creation(){

	### assertion check: instance is in the ACTIVE state
        status=1
        count=0
	    wait_time=60

        #while [ $count -lt 5 ]; do

         #       echo_time "${IMAGE_NAME} image is not in ACTIVE state (status $status)!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
        sleep ${wait_time}
		openstack image list | grep ${IMAGE_NAME} | sed 's/|//g'|awk '{print $NF}'|grep "active"
                status=$?

          #      let "count=count+1"
		#wait_time=$(( 2*$count ))
                

        #done

        ret_assert=$(assert $status "image_active")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${IMAGE_NAME} image is ACTIVE...great!" >> $STD_OUT_FILE
        fi

}

check_keypair_creation(){

	### assertion check: instance is in the ACTIVE state
        status=1
        count=0
	    wait_time=60

        #while [ $count -lt 5 ]; do
        sleep ${wait_time}
         #       echo_time "${KEY_NAME} key-pair is not still created (status $status)!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
		openstack keypair list | grep ${KEY_NAME}
                status=$?

        #        let "count=count+1"
		#wait_time=$(( 2*$count ))
                #sleep ${wait_time}

        #done

        ret_assert=$(assert $status "keypair")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${KEY_NAME} key-pair was created successfully...great!" >> $STD_OUT_FILE
        fi

}

check_security_group(){

	### assertion check: instance is in the ACTIVE state
    status=1
    count=0
	wait_time=60

        #while [ $count -lt 5 ]; do
        sleep ${wait_time}
         #       echo_time "${KEY_NAME} key-pair is not still created (status $status)!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
		openstack security group list|grep ${SECURITY_GROUP_NAME}
		status=$?

            #    let "count=count+1"
	#	wait_time=$(( 2*$count ))
                #sleep ${wait_time}
	
     #   done

        ret_assert=$(assert $status "security_group")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${SECURITY_GROUP_NAME} security group was created successfully...great!" >> $STD_OUT_FILE
        fi

}

check_private_network_active(){
	### assertion check: instance is in the ACTIVE state
	status=1
	count=0
	wait_time=60
	private_net_status="unknown"
	#while [ $count -lt 5 ]; do

	#	echo_time "${PRIVATE_NETWORK_NAME} private network is not in ACTIVE state (status ${private_net_status})!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
        sleep ${wait_time}
		private_net_status=$(openstack network show ${PRIVATE_NETWORK_NAME}|grep "status"|sed 's/|//g'|awk '{print $2}')

		echo ${private_net_status} | grep "ACTIVE" > /dev/null 2>&1
		status=$?
	#	let "count=count+1"
	#	wait_time=$(( 2*$count ))
    #                sleep ${wait_time}

	#done

        ret_assert=$(assert $status "net_active")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${PRIVATE_NETWORK_NAME} network is ACTIVE...great!" >> $STD_OUT_FILE
        fi
}

create_and_check_private_subnet(){

	### assertion check: instance is in the ACTIVE state
	status=1
	count=0
	#wait_time=60

	#while [ $count -lt 5 ]; do

	#	echo_time "${PRIVATE_SUBNET_NAME} private subnet is still not created (status ${status})!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
     #   sleep ${wait_time}
		#neutron subnet-create ${PRIVATE_NETWORK_NAME} ${PRIVATE_SUBNET_RANGE} --name ${PRIVATE_SUBNET_NAME} --dns-nameserver 8.8.4.4 --gateway ${PRIVATE_SUBNET_GATEWAY}
		openstack subnet list | grep ${PRIVATE_SUBNET_NAME}
		status=$?

	#	let "count=count+1"
	#	wait_time=$(( 2*$count ))
    #            sleep ${wait_time}

	#done

        ret_assert=$(assert $status "subnet_created")
        if [ ${ret_assert} -eq 0 ]; then
	    echo_time "${PRIVATE_SUBNET_NAME} private subnet is created...great!" >> $STD_OUT_FILE
        fi
}

check_router_active(){
	### assertion check: instance is in the ACTIVE state
	status=1
	count=0
	wait_time=60
	router_status="unknown"

	#while [ $count -lt 5 ]; do
    sleep ${wait_time}
	#	echo_time "${ROUTER_NAME} router is not in ACTIVE state (status ${router_status})!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE

		router_status=$(openstack router show ${ROUTER_NAME} | grep "status" | sed 's/|//g' | awk '{print $2}')

		echo ${router_status} | grep "ACTIVE" > /dev/null 2>&1
		status=$?
	#	let "count=count+1"
	#	wait_time=$(( 2*$count ))
    #            sleep ${wait_time}

	#done

        ret_assert=$(assert $status "router_active")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${ROUTER_NAME} router is ACTIVE...great!" >> $STD_OUT_FILE
        fi
}

create_and_check_router_port(){
        
	status=1
    count=0
	#wait_time=60

        #while [ $count -lt 5 ]; do
        #sleep ${wait_time}
         #       echo_time "${ROUTER_NAME} router has still no interfaces on ${PRIVATE_SUBNET_NAME} (status ${status})!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
		
		#router_interface_cmd_result=$(neutron router-interface-add ${ROUTER_NAME} ${PRIVATE_SUBNET_NAME})
		router_interface_cmd_result=$(launch_and_check_pipe "openstack router add subnet ${ROUTER_NAME} ${PRIVATE_SUBNET_NAME}")
		#router_port=$(echo ${router_interface_cmd_result} | awk '{print $3}')
		#neutron router-port-list ${ROUTER_NAME} | grep ${router_port} > /dev/null 2>&1
		status=$?

          #      let "count=count+1"
		#wait_time=$(( 2*$count ))
         #       sleep ${wait_time}
	
        #done

        ret_assert=$(assert $status "router_interface_created")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${router_port} was added to ${ROUTER_NAME}...great!" >> $STD_OUT_FILE
        fi
}



check_active_instance(){
	### assertion check: instance is in the ACTIVE state
	status=1
	count=0
	wait_time=120
	instance_status="unknown"

	#while [ $count -lt 5 ]; do
    sleep ${wait_time}
	#	echo_time "${INSTANCE_NAME} instance is not in ACTIVE state (status ${instance_status})!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
		instance_status=$(nova show ${INSTANCE_NAME} |grep status|awk '{print $4}')

		echo ${instance_status} | grep "ACTIVE" > /dev/null 2>&1
		status=$?
	#	let "count=count+1"
	#	wait_time=$(( 2*$count ))
    #            sleep ${wait_time}

	#done

        ret_assert=$(assert $status "instance_active")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${INSTANCE_NAME} instance is ACTIVE...great!" >> $STD_OUT_FILE
        fi
}

check_volume_creation(){

	### assertion check: instance is in the ACTIVE state
    status=1
    count=0
	wait_time=240
	volume_status="unknown"

        #while [ $count -lt 5 ]; do
    sleep ${wait_time}
         #       echo_time "${VOLUME_NAME} volume status is not 'available' (status ${volume_status})!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
		volume_status=$(openstack volume list|grep "${VOLUME_NAME}" | sed 's/|//g' | awk '{print $3}')

		echo ${volume_status} | grep "available"
                status=$?
        #        let "count=count+1"
		#wait_time=$(( 2*$count ))
        #        sleep ${wait_time}

        #done

        ret_assert=$(assert $status "volume_created")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${VOLUME_NAME} volume status is 'available'...great!" >> $STD_OUT_FILE
        fi

}

check_volume_attaching(){

        ### assertion check: instance is in the ACTIVE state
        status=1
        count=0
	    wait_time=60
        volume_attached_status="unknown"

        #while [ $count -lt 5 ]; do
        sleep ${wait_time}
         #       echo_time "${VOLUME_NAME} volume status is not 'available' (status ${volume_attached_status})!...retry (#$count) wait: ${wait_time} sec" >> $STD_OUT_FILE
                volume_attached_status=$(openstack volume list|grep "${VOLUME_NAME}"| sed 's/|//g' | awk '{print $5}')

                echo ${volume_attached_status} | grep "Attached"
                status=$?
         #       let "count=count+1"
		#wait_time=$(( 2*$count ))
        #        sleep ${wait_time}
        #done

        ret_assert=$(assert $status "volume_attached")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${VOLUME_NAME} volume status is 'attached'...great!" >> $STD_OUT_FILE
        fi

}

create_and_check_floating_ip_creation(){

	WORKLOAD_FLOATING_IP=""; 
	count=1;
	#wait_time=60
	status=1;

	#while [ $count -lt 5 ]; do
    #sleep ${wait_time}
		#WORKLOAD_FLOATING_IP=$(launch_and_check_pipe "openstack floating ip create --project ${PROJECT_NAME} ${PUBLIC_NETWORK_NAME}" | grep -w "floating_ip_address"| awk -F "|" '{print $3}'|tr -d '\040\011\012\015')
		WORKLOAD_FLOATING_IP=$(launch_and_check_pipe "openstack floating ip create --floating-ip-address ${FIP} --project ${PROJECT_NAME} ${PUBLIC_NETWORK_NAME}" | grep -w "floating_ip_address"| awk -F "|" '{print $3}'|tr -d '\040\011\012\015')
		status=$?
        sleep 10

	#	let "count=count+1" 
	#	wait_time=$(( 2*$count ))
    #            sleep ${wait_time}

	#done

        if [ -z "${WORKLOAD_FLOATING_IP}" ]; then
            #WORKLOAD_FLOATING_IP=$(launch_and_check_pipe "openstack floating ip create --project ${PROJECT_NAME} ${PUBLIC_NETWORK_NAME}" | grep -w "floating_ip_address"| awk -F "|" '{print $3}'|tr -d '\040\011\012\015')
            WORKLOAD_FLOATING_IP=$(launch_and_check_pipe "openstack floating ip create --floating-ip-address ${FIP} --project ${PROJECT_NAME} ${PUBLIC_NETWORK_NAME}" | grep -w "floating_ip_address"| awk -F "|" '{print $3}'|tr -d '\040\011\012\015')
            sleep 10
        fi

        ret_assert=$(assert $status "floating_ip_created")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "Created floating IP ${WORKLOAD_FLOATING_IP}...great!" >> $STD_OUT_FILE
        fi
}

add_and_check_floating_ip(){

	count=1;
	wait_time=60
	status=1;
	
	#while [ $count -lt 5 ]; do
    sleep ${wait_time}
		#nova add-floating-ip ${INSTANCE_NAME} ${WORKLOAD_FLOATING_IP} >> $STD_OUT_FILE 2>&1
		launch_and_check "openstack ip floating add ${WORKLOAD_FLOATING_IP} ${INSTANCE_NAME}"
		status=$?
		#let "count=count+1" 
		#wait_time=$(( 2*$count ))
        #        sleep ${wait_time}

	#done
        ret_assert=$(assert $status "floating_ip_added")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "Added floating IP ${WORKLOAD_FLOATING_IP} to instance ${INSTANCE_NAME}...great!" >> $STD_OUT_FILE
        fi
}



check_ssh(){
	### assertion check: instance is SSH-ABLE
	status=1
	count=0
	max_retry=10
	wait_time=120

	#while  [ $count -lt ${max_retry} ]; do
	sleep ${wait_time}	
		ssh -i /tmp/${KEY_NAME}.key cirros@${WORKLOAD_FLOATING_IP} -o 'UserKnownHostsFile=/dev/null' -o 'StrictHostKeyChecking=no' -o 'BatchMode=yes' -o 'ConnectionAttempts=1' true >> $STD_OUT_FILE 2>&1
		status=$?
		#echo_time "SSH connection for instance ${INSTANCE_NAME} result => ${status} [try: $count wait: ${wait_time} sec]" >> $STD_OUT_FILE

	#	let "count=count+1"
	#	wait_time=$(( 2*$count ))
	#	sleep ${wait_time}
	#done

        ret_assert=$(assert $status "ssh")
        if [ ${ret_assert} -eq 0 ]; then
            echo_time "${INSTANCE_NAME} instance ssh successfully...great!" >> $STD_OUT_FILE
        fi
}

echo_time "Remove old log file for workload..."
rm -rf /tmp/openstack_demo_workload-*


echo_time "Create new log file for workload..."
#flush log file
> $STD_ERR_FILE
> $STD_OUT_FILE



#    Steps:
#    1. Create image
#    2. Create keypair
#    3. Boot instance with keypair and get list of instances
#    4. Create volume and show list of volumes
#    5. Attach volume to instance and getlist of volumes
#    6. Add IP to instance
#    7. Create and add security group to instance
#    8. Check SSH connection to instance
#    9. Reboot instance
#    10. Check SSH connection to instance after reboot

echo_time "Workload started!" >> $STD_OUT_FILE

#source /root/keystonerc_admin
#source ${KEYSTONE_ADMIN_FILE_path}"/"${KEYSTONE_ADMIN_FILE}
source /tmp/${admin_keystonrc_file_name}

#1. Create image

echo_time "Create image ${IMAGE_NAME}..." >> $STD_OUT_FILE
launch_and_check "openstack image create --public --disk-format qcow2 --container-format bare --file ${IMAGE_FILE} $IMAGE_NAME"

####
check_image_creation
####

#source /root/keystonerc_demo
source /tmp/${keystonrc_file_name}

#2. Create keypair

echo_time "Create keypair ${KEY_NAME}..." >> $STD_OUT_FILE

ssh-keygen -b 2048 -t rsa -f /tmp/${KEY_NAME}.key -q -N ""

launch_and_check "openstack keypair create --public-key /tmp/${KEY_NAME}.key.pub ${KEY_NAME}"

####
check_keypair_creation
####

#3. Boot instance with keypair and get list of instances and
#7. Create and add security group to instance

echo_time "Create security group with SSH enabled" >> $STD_OUT_FILE
launch_and_check "openstack security group create ${SECURITY_GROUP_NAME}"
launch_and_check "openstack security group rule create --proto tcp --dst-port 22 ${SECURITY_GROUP_NAME}"

####
check_security_group
####

### create private network and subnet... the instance will be created using those one.

#source /root/keystonerc_admin
#source ${KEYSTONE_ADMIN_FILE_path}"/"${KEYSTONE_ADMIN_FILE}
source /tmp/${admin_keystonrc_file_name}

launch_and_check "openstack network set --external public"

#neutron net-create ${PRIVATE_NETWORK_NAME}
#source /root/keystonerc_demo
source /tmp/${keystonrc_file_name}

launch_and_check "openstack network create ${PRIVATE_NETWORK_NAME}"

###
check_private_network_active
###

echo_time "Create subnet '${PRIVATE_SUBNET_NAME}' on network '${PRIVATE_NETWORK_NAME}' with range '${PRIVATE_SUBNET_RANGE}'..." >> $STD_OUT_FILE

launch_and_check "openstack subnet create --subnet-range ${PRIVATE_SUBNET_RANGE} --network ${PRIVATE_NETWORK_NAME} --dns-nameserver 8.8.4.4 ${PRIVATE_SUBNET_NAME}"
###
create_and_check_private_subnet
###

# Create router to test network connections

echo_time "Create router ${ROUTER_NAME} for instance ${INSTANCE_NAME}..." >> $STD_OUT_FILE

#neutron router-create ${ROUTER_NAME}
launch_and_check "openstack router create ${ROUTER_NAME}"

###
check_router_active
###

###
create_and_check_router_port
###

launch_and_check "neutron router-gateway-set ${ROUTER_NAME} ${PUBLIC_NETWORK_NAME}"

#### Create instance

echo_time "Create instance ${INSTANCE_NAME} and boot it."  >> $STD_OUT_FILE
echo_time "" >> $STD_OUT_FILE
echo_time "Details: " >> $STD_OUT_FILE
echo_time "........image name = ${IMAGE_NAME}" >> $STD_OUT_FILE
echo_time "........network = ${PRIVATE_NETWORK_NAME}" >> $STD_OUT_FILE
echo_time "........security group = ${SECURITY_GROUP_NAME}" >> $STD_OUT_FILE
echo_time "........key name = ${KEY_NAME}" >> $STD_OUT_FILE

launch_and_check "openstack server create --flavor m1.tiny --image ${IMAGE_NAME} --nic net-id=${PRIVATE_NETWORK_NAME} --security-group ${SECURITY_GROUP_NAME} --key-name ${KEY_NAME} ${INSTANCE_NAME}"
#openstack server create --flavor m1.tiny --image ${IMAGE_NAME} --nic net-id=private --security-group ${SECURITY_GROUP_NAME} --key-name ${KEY_NAME} ${INSTANCE_NAME} >> $STD_OUT_FILE 2>&1

######
check_active_instance
#####

# 6. Add IP to instance
echo_time "Create floating ip for instance ${INSTANCE_NAME}..." >> $STD_OUT_FILE

#source /root/keystonerc_admin
#source ${KEYSTONE_ADMIN_FILE_path}"/"${KEYSTONE_ADMIN_FILE}
source /tmp/${admin_keystonrc_file_name}

####
create_and_check_floating_ip_creation
####

#source /root/keystonerc_demo
source /tmp/${keystonrc_file_name}

echo_time "Add floating IP ${WORKLOAD_FLOATING_IP} to instance ${INSTANCE_NAME}..." >> $STD_OUT_FILE

####
add_and_check_floating_ip
####


echo_time "List all instances on tenants..." >> $STD_OUT_FILE
launch_and_check "nova list"

#4. Create volume and show list of volumes

echo_time "Create volume ${VOLUME_NAME}..." >> $STD_OUT_FILE
launch_and_check "openstack volume create --image ${IMAGE_NAME} --size ${VOLUME_SIZE} --availability-zone ${AVAILABILITY_ZONE} ${VOLUME_NAME}"

####
check_volume_creation
###

echo_time "Show volume list..." >> $STD_OUT_FILE
launch_and_check "openstack volume list"

# 5. Attach volume to instance and getlist of volumes
echo_time "Attach volume ${VOLUME_NAME} to ${INSTANCE_NAME}..." >> $STD_OUT_FILE
launch_and_check "openstack server add volume ${INSTANCE_NAME} ${VOLUME_NAME} --device /dev/vdb"

####
check_volume_attaching
###

echo_time "Show volume list..." >> $STD_OUT_FILE
launch_and_check "openstack volume list"

#8. Check SSH connection to instance

echo_time "Check SSH connection for instance ${INSTANCE_NAME} (before reboot)" >> $STD_OUT_FILE

#####
check_ssh
#####

#9. reboot instance and check again ssh connection
echo_time "Reboot instance ${INSTANCE_NAME}" >> $STD_OUT_FILE
launch_and_check "openstack server reboot --hard ${INSTANCE_NAME}"

###
check_active_instance
###

echo_time "Check SSH connection for instance ${INSTANCE_NAME} (after reboot)" >> $STD_OUT_FILE

#####
check_ssh
#####

### If there is no failed assertions 
echo_time "Assertion results: OK" >> $STD_OUT_FILE


echo_time "Start resources cleanup" >> $STD_OUT_FILE

#./openstack_pike_environment_cleanup_notempest.sh >> $STD_OUT_FILE 2>&1
#source /root/keystonerc_demo
source /tmp/${keystonrc_file_name}

launch_and_check "openstack ip floating delete ${WORKLOAD_FLOATING_IP}"
echo_time "Removed floating ip ${WORKLOAD_FLOATING_IP}" >> $STD_OUT_FILE

#source /root/keystonerc_admin
#source ${KEYSTONE_ADMIN_FILE_path}"/"${KEYSTONE_ADMIN_FILE}
source /tmp/${admin_keystonrc_file_name}

INSTANCE_DELETE=$(launch_and_check_pipe "nova list --all-tenant" |grep -i "${INSTANCE_NAME}"|awk '{print $2}')
launch_and_check "nova delete ${INSTANCE_DELETE}"
#launch_and_check "nova delete ${INSTANCE_NAME}"
echo_time "Cleaned tempest created instance ${INSTANCE_NAME}" >> $STD_OUT_FILE

#IMAGE_DELETE=$(launch_and_check_pipe "openstack image list" |grep "${IMAGE_NAME}"|awk '{print $2}')
#launch_and_check "openstack image delete ${IMAGE_DELETE}"
launch_and_check "openstack image delete ${IMAGE_NAME}"
echo_time "Cleaned tempest created images ${IMAGE_NAME}" >> $STD_OUT_FILE

#VOLUME_DELETE=$(launch_and_check_pipe "cinder list --all-tenant" |grep -i "${VOLUME_NAME}"|awk '{print $2}')
#launch_and_check "cinder delete ${VOLUME_DELETE}"
sleep 30
launch_and_check "cinder delete ${VOLUME_NAME}"
echo_time "Cleaned tempest created volumes ${VOLUME_NAME}" >> $STD_OUT_FILE



echo_time "Clean tempest created routers and networks..." >> $STD_OUT_FILE
ROUTERS=${ROUTER_NAME}
NETWORKS=${PRIVATE_NETWORK_NAME}

for ROUTER in $ROUTERS; do
        launch_and_check "openstack router unset --external-gateway $ROUTER"
        for PORT in $(launch_and_check_pipe "openstack port list --router $ROUTER --format=value -c ID"); do
                launch_and_check "openstack router remove port $ROUTER $PORT"
                echo_time "Removed port $PORT on router $ROUTER" >> $STD_OUT_FILE
                sleep 5
        done
        launch_and_check "openstack router delete $ROUTER"
        echo_time "Removed router $ROUTER" >> $STD_OUT_FILE
done

for NETWORK in $NETWORKS; do
        for PORT in $(launch_and_check_pipe "openstack port list --network $NETWORK --format=value -c ID"); do
                launch_and_check "openstack port delete $PORT"
                echo_time "Removed port $PORT" >> $STD_OUT_FILE
                sleep 5
        done
        #wait $(jobs -p)
        launch_and_check "openstack network delete $NETWORK"
        echo_time "Removed network $NETWORK" >> $STD_OUT_FILE 2>&1
done

#remove security group
launch_and_check "openstack security group delete ${SECURITY_GROUP_NAME}"
echo_time "Removed security group ${SECURITY_GROUP_NAME}" >> $STD_OUT_FILE

#delete tempest-pycast_keypair keypair
#source /root/keystonerc_demo
source /tmp/${keystonrc_file_name}

launch_and_check "openstack keypair delete ${KEY_NAME}"

rm -rf /tmp/${KEY_NAME}.key
rm -rf /tmp/${KEY_NAME}.key.pub

echo_time "Removed keypair ${KEY_NAME}" >> $STD_OUT_FILE

# delete create domain, user, project, role
#source ${KEYSTONE_ADMIN_FILE_path}"/"${KEYSTONE_ADMIN_FILE}
source /tmp/${admin_keystonrc_file_name}

launch_and_check "openstack user delete ${USER_NAME}"
echo_time "Removed user ${USER_NAME}" >> $STD_OUT_FILE

launch_and_check "openstack project delete ${PROJECT_NAME}"
echo_time "Removed project ${PROJECT_NAME}" >> $STD_OUT_FILE

launch_and_check "openstack domain set --disable ${DOMAIN_NAME}"
echo_time "Disabled domain ${DOMAIN_NAME}" >> $STD_OUT_FILE

launch_and_check "openstack domain delete ${DOMAIN_NAME}"
echo_time "Removed domain ${DOMAIN_NAME}" >> $STD_OUT_FILE

#remove credential files for user and admin
rm -rf /tmp/${keystonrc_file_name}
rm -rf /tmp/${admin_keystonrc_file_name}

echo_time "End resources cleanup" >> $STD_OUT_FILE

echo_time "Workload terminated!" >> $STD_OUT_FILE
exit 0
