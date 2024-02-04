#! /bin/bash


export LABEL_PATH="/dev/disk/by-label/"
export MOUNT_PATH="/run/mount/"
export RUN_DIR="/tmp/disk_mounter"

STATUS_ERROR="MOUNT_ERROR"
STATUS_MOUNTED="MOUNTED"
STATUS_NOT_MOUNTED="NOT_MOUNTED"

MQTT_PREFIX="disk-mounter"
MQTT_DEVICES_FIELD="devices"
MQTT_STATUS_FIELD="status"
MQTT_USED_FIELD="used"
MQTT_USED_PER_FIELD="used_per"
MQTT_SIZE_FIELD="size"
MQTT_AVAILABLE_FIELD="available"
MQTT_MOUNT_COMMAND="mount"
MQTT_SERVER=$(snd MQTT-BROKER)

AVAILABLE_PARTITIONS="?"


# subcribe mount commans
mkdir -p $RUN_DIR
mosquitto_sub -t ${MQTT_PREFIX}/+/${MQTT_MOUNT_COMMAND} -F "%t %p"  --host ${MQTT_SERVER} | while read command value 
do
    echo $value > $RUN_DIR/$(echo $command | sed "s/${MQTT_PREFIX}\///g" | sed "s/\//_/g")
done &


# Main loop
while sleep 1
do
    # iterate found partitions
    AVAILABLE_PARTITIONS_AUX="${AVAILABLE_PARTITIONS}"
    AVAILABLE_PARTITIONS=""

    if [ "$(ls ${LABEL_PATH} 2> /dev/null )" != "" ]
    then
        for PART_LABEL in $(ls -1 ${LABEL_PATH})
        do
            # Check partition mount requirement
            MOUNT_PART_MEM="${RUN_DIR}/${PART_LABEL}_${MQTT_MOUNT_COMMAND}"
            if [ ! -f  "${MOUNT_PART_MEM}" ]
            then 
                MOUNT_PART="0"
            else
                MOUNT_PART=$(cat ${MOUNT_PART_MEM})
            fi


            # Get mount value
            CURRENT_STATUS_VAR=STATUS_${PART_LABEL}_VAR_NAME
            CURRENT_SIZE_VAR=SIZE_${PART_LABEL}_VAR_NAME
            CURRENT_USED_VAR=USED_${PART_LABEL}_VAR_NAME
            CURRENT_AVAILABLE_VAR=AVAILABLE_${PART_LABEL}_VAR_NAME
            CURRENT_SIZE_PER_VAR=SIZE_PER_${PART_LABEL}_VAR_NAME
            if findmnt ${LABEL_PATH}${PART_LABEL} > /dev/null
            then
                
                # Check if external mount
                if [ ! -d ${MOUNT_PATH}${PART_LABEL} ]
                then
                    continue
                fi


                # Set disk status
                STATUS="${STATUS_MOUNTED}"
                DISK_INFO=$(df -h  | grep "${MOUNT_PATH}${PART_LABEL}$" | sed "s/  */ /g")


                # report size
                SIZE=$(echo ${DISK_INFO} | cut -d " " -f 2)
                if [ "${SIZE}" != "${!CURRENT_SIZE_VAR}" ]
                then
                    export ${CURRENT_SIZE_VAR}="${SIZE}"
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_SIZE_FIELD} -m "${SIZE}" --host ${MQTT_SERVER}
                fi

                # report used
                USED=$(echo ${DISK_INFO} | cut -d " " -f 3)
                if [ "${USED}" != "${!CURRENT_USED_VAR}" ]
                then
                    export ${CURRENT_USED_VAR}="${USED}"
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_USED_FIELD} -m "${USED}" --host ${MQTT_SERVER}
                fi

                # report available
                AVAILABLE=$(echo ${DISK_INFO} | cut -d " " -f 4)
                if [ "${AVAILABLE}" != "${!CURRENT_AVAILABLE_VAR}" ]
                then
                    export ${CURRENT_AVAILABLE_VAR}="${AVAILABLE}"
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_AVAILABLE_FIELD} -m "${AVAILABLE}" --host ${MQTT_SERVER}
                fi

                # report used%
                USED_PER=$(echo ${DISK_INFO} | cut -d " " -f 5)
                if [ "${USED_PER}" != "${!CURRENT_SIZE_PER_VAR}" ]
                then
                    export ${CURRENT_SIZE_PER_VAR}="${USED_PER}"
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_USED_PER_FIELD} -m "${USED_PER}" --host ${MQTT_SERVER}
                fi

            else
                STATUS=${!CURRENT_STATUS_VAR}

                if [ "${!CURRENT_SIZE_VAR}" != "" ]
                then
                    unset ${CURRENT_SIZE_VAR}
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_SIZE_FIELD} -m ""  --host ${MQTT_SERVER}
                fi
                if [ "${!CURRENT_USED_VAR}" != "" ]
                then
                    unset ${CURRENT_USED_VAR}
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_USED_FIELD} -m "" --host ${MQTT_SERVER}
                fi
                if [ "${!CURRENT_AVAILABLE_VAR}" != "" ]
                then
                    unset ${CURRENT_AVAILABLE_VAR}
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_AVAILABLE_FIELD} -m "" --host ${MQTT_SERVER}
                fi
                if [ "${!CURRENT_SIZE_PER_VAR}" != "" ]
                then
                    unset ${CURRENT_SIZE_PER_VAR}
                    mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_USED_PER_FIELD} -m "" --host ${MQTT_SERVER}
                fi           
            fi


            # Check if need to mount
            if [ "${STATUS}" == "${STATUS_NOT_MOUNTED}" ] && [ "${MOUNT_PART}" == "1" ]
            then
                echo "Mounting..."
                mkdir -p "${MOUNT_PATH}${PART_LABEL}"
                mount "${LABEL_PATH}${PART_LABEL}" "${MOUNT_PATH}${PART_LABEL}"
                chmod a+rw "${MOUNT_PATH}${PART_LABEL}"

                if findmnt ${LABEL_PATH}${PART_LABEL} > /dev/null
                then
                    echo "mounted '${LABEL_PATH}${PART_LABEL}' at '${MOUNT_PATH}${PART_LABEL}'"
                    STATUS="${STATUS_MOUNTED}"
                else
                    echo "mount error '${LABEL_PATH}${PART_LABEL}'"
                    STATUS="${STATUS_ERROR}"
                fi

            elif [ "${STATUS}" != "${STATUS_NOT_MOUNTED}" ] && [ "${MOUNT_PART}" == "0" ]
            then
                if findmnt ${LABEL_PATH}${PART_LABEL} > /dev/null
                then
                    echo "Unmounting..."
                    umount ${LABEL_PATH}${PART_LABEL}
                    echo "unmounted '${LABEL_PATH}${PART_LABEL}' from '${MOUNT_PATH}${PART_LABEL}'"
                fi

                STATUS="${STATUS_NOT_MOUNTED}"

            fi


            # Report if change status
            if [ "${STATUS}" != "${!CURRENT_STATUS_VAR}" ]
            then
                export ${CURRENT_STATUS_VAR}="${STATUS}"
                mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${PART_LABEL}/${MQTT_STATUS_FIELD} -m "${STATUS}" --host ${MQTT_SERVER}
            fi


            # Append data
            AVAILABLE_PARTITIONS="${AVAILABLE_PARTITIONS}${PART_LABEL};"

        done
    fi


    # Report if changes
    if [ "${AVAILABLE_PARTITIONS}" != "${AVAILABLE_PARTITIONS_AUX}" ]
    then
        mosquitto_pub --qos 1 -r -t ${MQTT_PREFIX}/${MQTT_DEVICES_FIELD} -m "${AVAILABLE_PARTITIONS}" --host ${MQTT_SERVER}
    fi

done
