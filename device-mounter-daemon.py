#! /usr/bin/env python3
# 
# This file is part of the device-mounter-daemon distribution.
# Copyright (c) 2023 Javier Moreno Garcia.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import d2dcn
import argparse
import sys
import time
import os
import json


class deviceMounter():

    MOUNT_COMMAND_PREFIX = "mount/"
    UNMOUNT_COMMAND_PREFIX = "ummount/"
    DEVICE_INFO_PREFIX = "info/"

    LABEL_PATH = "/dev/disk/by-label/"
    MOUNT_PATH = "/run/mount/"
    ERROR_FIELD = "error"

    ERROR_CREATE_MOUNT_POINT = "Create mount point error"
    ERROR_MOUNT_COMMAND_ERROR = "Mount command error"
    ERROR_UMOUNT_COMMAND_ERROR = "unmount command error"

    class deviceInfo():
        IS_MOUNTED="is_mounted"
        USED="used"
        USED_PER="used_per"
        SIZE="size"
        AVAILABLE="available"


    def __init__(self, options):
        
        self.options = options
        self.d2d = d2dcn.d2d()

        self.devices = []
        self.removed_devices = []
        self.info_sent = {}
        self.is_mounted = {}


    def mountDevice(self, device):

        device_path = deviceMounter.LABEL_PATH + device
        device_mount_path = deviceMounter.MOUNT_PATH + device

        try:
            os.makedirs(device_mount_path, exist_ok=True)
        except:
            return {deviceMounter.ERROR_FIELD: deviceMounter.ERROR_CREATE_MOUNT_POINT}

        command = "mount " + device_path + " " + device_mount_path
        returned_value = os.system(command)

        if returned_value != 0:
            return {deviceMounter.ERROR_FIELD: deviceMounter.ERROR_MOUNT_COMMAND_ERROR}

        else:
            self.is_mounted[device] = True
            self.d2d.enableCommand(deviceMounter.MOUNT_COMMAND_PREFIX + device, not self.is_mounted[device])
            self.d2d.enableCommand(deviceMounter.UNMOUNT_COMMAND_PREFIX + device, self.is_mounted[device])
            return {}


    def umountDevice(self, device):

        device_mount_path = deviceMounter.MOUNT_PATH + "/" + device
        os.mkdir(device_mount_path, parents=True, exist_ok=True)

        command = "umount " + device_mount_path
        returned_value = os.system(command)

        if returned_value != 0:
            return {deviceMounter.ERROR_FIELD: deviceMounter.ERROR_UMOUNT_COMMAND_ERROR}

        else:
            self.is_mounted[device] = False
            self.d2d.enableCommand(deviceMounter.UNMOUNT_COMMAND_PREFIX + device, self.is_mounted[device])
            self.d2d.enableCommand(deviceMounter.MOUNT_COMMAND_PREFIX + device, not self.is_mounted[device])
            return {}


    def detectDeviceUpdates(self):

        new_devices = []
        removed_devices = []
        reconnected_devices = []

        if os.path.exists(deviceMounter.LABEL_PATH):

            os_devices = list(filter(lambda file : os.path.isfile(deviceMounter.LABEL_PATH + "/" + file),  os.listdir(deviceMounter.LABEL_PATH)))

            for file in os_devices:
                if file in self.removed_devices:
                    reconnected_devices.append(file)

                elif file not in self.devices:
                    new_devices.append(file)

            for device in self.devices:
                if device not in os_devices:
                    removed_devices.append(device)


            for removed_device in removed_devices:
                self.devices.remove(removed_device)

            for reconnected_device in reconnected_devices:
                self.removed_devices.remove(reconnected_device)

            self.devices += new_devices
            self.removed_devices += removed_devices

        return new_devices, removed_devices, reconnected_devices


    def addDeviceCommand(self, new_device):

        response = {}
        response[deviceMounter.ERROR_FIELD] = {}
        response[deviceMounter.ERROR_FIELD][d2dcn.d2dConstants.infoField.TYPE] = d2dcn.d2dConstants.valueTypes.STRING
        response[deviceMounter.ERROR_FIELD][d2dcn.d2dConstants.infoField.OPTIONAL] = True

        self.d2d.addServiceCommand(lambda args : self.mountDevice(new_device),
                                    deviceMounter.MOUNT_COMMAND_PREFIX + new_device,
                                    {}, response, d2dcn.d2dConstants.category.GENERIC, True)

        self.d2d.addServiceCommand(lambda args : self.umountDevice(new_device),
                                    deviceMounter.UNMOUNT_COMMAND_PREFIX + new_device,
                                    {}, response, d2dcn.d2dConstants.category.GENERIC, False)


    def disableRemovedDeviceCommand(self, removed_device):
        self.d2d.enableCommand(deviceMounter.MOUNT_COMMAND_PREFIX + removed_device, False)
        self.d2d.enableCommand(deviceMounter.UNMOUNT_COMMAND_PREFIX + removed_device, False)


    def enableRemovedDeviceCommand(self, reconnected_device):
        self.d2d.enableCommand(deviceMounter.MOUNT_COMMAND_PREFIX + reconnected_device, True)
        self.d2d.enableCommand(deviceMounter.UNMOUNT_COMMAND_PREFIX + reconnected_device, False)


    def updateMountedDeviceInfo(self, device):
        device_info = {}
        device_info[deviceMounter.deviceInfo.IS_MOUNTED] = False
        device_info[deviceMounter.deviceInfo.USED] = 0
        device_info[deviceMounter.deviceInfo.USED_PER] = 0
        device_info[deviceMounter.deviceInfo.SIZE] = 0
        device_info[deviceMounter.deviceInfo.AVAILABLE] = 0
        self.updateDeviceInfo(device, device_info)


    def updateUnmountedDeviceInfo(self, device):
        device_info = {}
        device_info[deviceMounter.deviceInfo.IS_MOUNTED] = False
        device_info[deviceMounter.deviceInfo.USED] = 0
        device_info[deviceMounter.deviceInfo.USED_PER] = 0
        device_info[deviceMounter.deviceInfo.SIZE] = 0
        device_info[deviceMounter.deviceInfo.AVAILABLE] = 0
        self.updateDeviceInfo(device, device_info)


    def updateDeviceInfo(self, device, device_info):

        json_str = json.dumps(device_info, indent=1)

        if device not in self.info_sent:
            self.info_sent[device] = ""

        if self.info_sent[device] != json_str:
            self.info_sent[device] = json_str
            self.d2d.publishInfo(deviceMounter.DEVICE_INFO_PREFIX + device, json_str, d2dcn.d2dConstants.category.GENERIC)


    def run(self):
        while time.sleep(1) == None:

            new_devices, removed_devices, reconnected_devices = self.detectDeviceUpdates()

            for new_device in new_devices:
                self.addDeviceCommand(new_device)

            for removed_device in removed_devices:
                self.disableRemovedDeviceCommand(removed_device)

            for reconnected_device in reconnected_devices:
                self.enableRemovedDeviceCommand(reconnected_device)

            for device in self.devices:
                self.updateMountedDeviceInfo(device)

            for device in self.removed_devices:
                self.updateUnmountedDeviceInfo(device)

            self.d2d.removeUnregistered()


def main():

    parser = argparse.ArgumentParser(description="Device mounter daemon")
    parser.add_argument(
        '--bool-option',
        required=False,
        default="",
        action="store_true",
        help='')

    parser.add_argument(
        '--device_pattern',
        metavar = "[DEVICE_PATTERN]",
        required=False,
        default="",
        help='Regular expresion for name')
 
    args = parser.parse_args(sys.argv[1:])
    dm = deviceMounter(args)
    dm.run()


# Main execution
if __name__ == '__main__':

    try:
        main()

    except KeyboardInterrupt:
        pass
