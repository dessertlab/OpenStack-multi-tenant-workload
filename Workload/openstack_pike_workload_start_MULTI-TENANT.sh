#!/bin/bash
cd "$(dirname "$0")"

echo "Remove old log file of OpenStack..."
truncate -s 0 /var/log/*.log
truncate -s 0 /var/log/*/*.log

echo "Remove old log file for workload..."
rm -rf /tmp/openstack_demo_workload-*
rm -rf /tmp/stdout_*
rm -rf /tmp/stderr_*

#user id
i=0;

echo "Starting User 1"
(./DEPL.sh 1) &

sleep 60
echo "Starting User 2"
(./Instance_Volume.sh 2) &


sleep 30
echo "Starting User 3"
(./Volume_Instance.sh 3) &


sleep 30
echo "Starting User 4"
(./Instance.sh 4) &


sleep 60
echo "Starting User 5"
(./Volume.sh 5) &

sleep 60
echo "Starting User 6"
(./Instance_Volume.sh 6) &

sleep 60
echo "Starting User 7"
(./Volume.sh 7) &


sleep 180
echo "Starting User 8"
(./Volume_Instance.sh 8) &


sleep 240
echo "Starting User 9"
(./Network.sh 9) &

sleep 180
echo "Starting User 10"
(./Network.sh 10) &

exit 0
