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
import shutil
import json


class container():
    pass

class deviceMounter():

    MOUNT_COMMAND = "mount"
    UNMOUNT_COMMAND = "ummount"

    LABEL_PATH = "/dev/disk/by-label/"
    MOUNT_PATH = "/run/mount/"
    SYSTEM_FSTAB_PATH = "/etc/fstab"
    SYSTEM_MOUNTED_PATH = "/proc/mounts"
    ERROR_FIELD = "error"

    INVALID_VALUE = ""

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
        self.d2d = d2dcn.d2d(service="DeviceMounter")

        self.devices = []
        self.removed_devices = []
        self.info_sent = {}
        self.is_mounted = {}
        self.system_mounted_devices = []
        self.device_info = {}

    def generateMountCommandName(device):
        return device + "." + deviceMounter.MOUNT_COMMAND


    def generateUnmountCommandName(device):
        return device + "." + deviceMounter.UNMOUNT_COMMAND


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
            self.d2d.enableCommand(deviceMounter.generateMountCommandName(device), not self.is_mounted[device])
            self.d2d.enableCommand(deviceMounter.generateUnmountCommandName(device), self.is_mounted[device])
            return {}


    def umountDevice(self, device):

        device_mount_path = deviceMounter.MOUNT_PATH + "/" + device

        command = "umount " + device_mount_path
        returned_value = os.system(command)

        if returned_value != 0:
            return {deviceMounter.ERROR_FIELD: deviceMounter.ERROR_UMOUNT_COMMAND_ERROR}

        else:
            self.is_mounted[device] = False
            self.d2d.enableCommand(deviceMounter.generateUnmountCommandName(device), self.is_mounted[device])
            self.d2d.enableCommand(deviceMounter.generateMountCommandName(device), not self.is_mounted[device])
            return {}


    def detectDeviceUpdates(self):

        new_devices = []
        removed_devices = []
        reconnected_devices = []

        if os.path.exists(deviceMounter.LABEL_PATH):

            os_devices = list(filter(lambda file : os.path.islink(deviceMounter.LABEL_PATH + "/" + file) and file not in self.system_mounted_devices, os.listdir(deviceMounter.LABEL_PATH)))

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

        response = d2dcn.commandArgsDef()
        response.add(deviceMounter.ERROR_FIELD, d2dcn.constants.valueTypes.STRING, True)


        self.d2d.addServiceCommand(lambda args : self.mountDevice(new_device),
                                    deviceMounter.generateMountCommandName(new_device),
                                    d2dcn.commandArgsDef(), response, new_device, True)

        self.d2d.addServiceCommand(lambda args : self.umountDevice(new_device),
                                    deviceMounter.generateUnmountCommandName(new_device),
                                    d2dcn.commandArgsDef(), response, new_device, False)

        self.device_info[new_device] = container()
        self.device_info[new_device].is_mounted = self.d2d.addInfoWriter(new_device + "." + deviceMounter.deviceInfo.IS_MOUNTED, d2dcn.constants.valueTypes.BOOL, new_device)
        self.device_info[new_device].used = self.d2d.addInfoWriter(new_device + "." + deviceMounter.deviceInfo.USED, d2dcn.constants.valueTypes.FLOAT, new_device)
        self.device_info[new_device].used_per = self.d2d.addInfoWriter(new_device + "." + deviceMounter.deviceInfo.USED_PER, d2dcn.constants.valueTypes.FLOAT, new_device)
        self.device_info[new_device].size = self.d2d.addInfoWriter(new_device + "." + deviceMounter.deviceInfo.SIZE, d2dcn.constants.valueTypes.FLOAT, new_device)
        self.device_info[new_device].available = self.d2d.addInfoWriter(new_device + "." + deviceMounter.deviceInfo.AVAILABLE, d2dcn.constants.valueTypes.FLOAT, new_device)

    def disableRemovedDeviceCommand(self, removed_device):
        self.d2d.enableCommand(deviceMounter.generateMountCommandName(removed_device), False)
        self.d2d.enableCommand(deviceMounter.generateUnmountCommandName(removed_device), False)


    def enableRemovedDeviceCommand(self, reconnected_device):
        self.d2d.enableCommand(deviceMounter.generateMountCommandName(reconnected_device), True)
        self.d2d.enableCommand(deviceMounter.generateUnmountCommandName(reconnected_device), False)


    def updateRegisteredDeviceInfo(self, device):

        if device in self.is_mounted and self.is_mounted[device]:

            total, used, free = shutil.disk_usage(deviceMounter.MOUNT_PATH + "/" + device)

            self.device_info[device].is_mounted.value = True
            self.device_info[device].used.value = round(used / (1024*1024*1024))
            self.device_info[device].used_per.value = round((used / total) * 100, 2)
            self.device_info[device].size.value = round(total / (1024*1024*1024))
            self.device_info[device].available.value = round(free / (1024*1024*1024))

        else:
            self.device_info[device].is_mounted.value = False


    def updateRemovedDeviceInfo(self, device):
        self.device_info[device].is_mounted = False


    def updateSystemMounted(self):

        # Get system mounted devices
        self.system_mounted_devices = []
        with open(deviceMounter.SYSTEM_FSTAB_PATH, "r") as file:
            proc_file_content = file.read()
        with open(deviceMounter.SYSTEM_MOUNTED_PATH, "r") as file:
            proc_file_content += file.read()
        for dev in os.listdir(deviceMounter.LABEL_PATH) if os.path.isdir(deviceMounter.LABEL_PATH) else []:
            real_dev = os.path.realpath(deviceMounter.LABEL_PATH + "/" + dev)

            if real_dev in proc_file_content or dev in proc_file_content:
                self.system_mounted_devices.append(dev)


    def run(self):

        self.updateSystemMounted()

        while True:

            new_devices, removed_devices, reconnected_devices = self.detectDeviceUpdates()

            for new_device in new_devices:
                self.addDeviceCommand(new_device)

            for removed_device in removed_devices:
                self.disableRemovedDeviceCommand(removed_device)

            for reconnected_device in reconnected_devices:
                self.enableRemovedDeviceCommand(reconnected_device)

            for device in self.devices:
                self.updateRegisteredDeviceInfo(device)

            for device in self.removed_devices:
                self.updateRemovedDeviceInfo(device)

            time.sleep(1)


def main():

    parser = argparse.ArgumentParser(description="Device mounter daemon")
    #parser.add_argument(
    #    '--bool-option',
    #    required=False,
    #    default="",
    #    action="store_true",
    #    help='')

    #parser.add_argument(
    #    '--device_pattern',
    #    metavar = "[DEVICE_PATTERN]",
    #    required=False,
    #    default="",
    #    help='Regular expresion for name')

    args = parser.parse_args(sys.argv[1:])
    dm = deviceMounter(args)
    dm.run()


# Main execution
if __name__ == '__main__':

    try:
        main()

    except KeyboardInterrupt:
        pass
