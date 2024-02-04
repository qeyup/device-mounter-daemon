#!/bin/bash

COMMAND="sudo docker-compose -p device_mounter_dwc -f docker/docker-compose.yml up -d"
if type konsole &> /dev/null; then konsole -e "${COMMAND}";
elif type xterm &> /dev/null; then xterm -e "${COMMAND}";
else ${COMMAND}; fi
