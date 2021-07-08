# Import packages
import time
import os
from glob import glob
from subprocess import check_output, CalledProcessError
from datetime import datetime
from distutils.dir_util import copy_tree
import shutil
from shutil import copytree
import logging

def get_usb_devices():
    sdb_devices = map(os.path.realpath, glob('/sys/block/sd*'))
    usb_devices = (dev for dev in sdb_devices
        if 'usb' in dev.split('/')[5])
    return dict((os.path.basename(dev), dev) for dev in usb_devices)

def get_mount_points(devices=None):
    devices = devices or get_usb_devices()  # if devices are None: get_usb_devices
    output = check_output(['mount']).splitlines()
    output = [tmp.decode('UTF-8') for tmp in output]
    def is_usb(path):
        return any(dev in path for dev in devices)
    usb_info = (line for line in output if is_usb(line.split()[0]))
    return [(info.split()[0], info.split()[2]) for info in usb_info]

# Print the welcome message
print("Please insert the drive to be copied...")
# Establish the state of the program
state = "waitingForCopy"
# Get the config file details
with open('config.txt') as f:
    lines = [line.rstrip() for line in f]
# Get the drive name
drive_name = lines[0].split(":",1)[1].strip()
# Establish the number of files in the current operation
file_count = 0

# Check if a drive is there to be copied
def checkCopy():
    # Try 
    try: 
        # Get the config file details
        with open('config.txt') as f:
            lines = [line.rstrip() for line in f]
        # Get the drive name
        drive_name = lines[0].split(":",1)[1].strip()
        # Get the drives plugged into the computer
        drives = get_mount_points()
        # For every drive
        for drive in drives:
            # If the drive has the searched for name
            if drive_name in drive[1]:
                # Print that the drive was found
                print("Drive",drive_name,"found.")
                # Get the name of the project
                project_name = input("Type the name and reference number of the project: ")
                # While the project name isn't valid
                while not validateProjectName(project_name):
                    # Get a new project name
                    project_name = input("Type the name and reference number of the project, ensuring it is formatted correctly: ")
                # Copy the footage and return the new state
                return copyFootage(drive, project_name)
        # Return the new state
        return "waitingForCopy"
    # If there's an error
    except Exception as error: 
        # Open the error log file
        with open('errorLog.txt', 'a') as the_file:
            # Add the date and the error to the log
            the_file.write(datetime.now(),error,'\n')
        # Print the error
        print(error)
        # Return the error state
        return "error"

# Create a folder with the given name and copy the footage
def copyFootage(drive, project_name):
    # Get the config file details
    with open('config.txt') as f:
        lines = [line.rstrip() for line in f]
    # Get the path to copy to
    copy_path = os.path.join(lines[1].split(":",1)[1].strip(),project_name)
    # Unmask the os so that the copying results can be accessed by any user
    os.umask(0)

    ## CHANGE ME
    drive_path = os.path.expanduser("~/Documents/backup/mockDrive")

    # Get the values of the disk at the destination
    total, used, free = shutil.disk_usage(os.path.expanduser(lines[1].split(":",1)[1].strip()))
    # Print the space available in GB
    print("Space available: ", free)
    # Print the space available in GB
    print("Footage size: ", os.path.getsize(drive_path))
    # If there is enough space at the destination (with 20% extra space)
    if (free > os.path.getsize(drive_path)*1.2):
        # Create a file counter
        global file_count
        file_count = 0
        # For each file
        for root, dirs, files in os.walk(drive_path):
            # Increment the number of files
            file_count += len(files)
            # Increment the number of directories
            file_count += len(dirs)
        # Print the number of files
        print("Number of files: ",file_count)
        # Print that the footage is being copied
        print("Copying footage...")
        # Copy the contents from the drive to the provided location
        copytree(drive_path, os.path.expanduser(copy_path), ignore=updateProgress)
        # Return a success
        return "copyComplete"
    else:
        # Return there wasn't enough space?
        return "notEnoughSpace"

def updateProgress(path, names):
    print(path)
    return []   # nothing will be ignored

# Pause until the drive has been removed
def waitRemove(message):
    # Print the provided message
    print(message)
    # Create a variable to store whether the drive is present
    drive_present = False
    # Get the drives plugged into the computer
    drives = get_mount_points()
    # For every drive
    for drive in drives:
        # If the drive has the searched for name
        if drive_name in drive[1]:
            # Log the drive as present
            drive_present = True
    # While the drive is pesent
    while drive_present:
        # Set the drive present as false
        drive_present = False
        # Wait 1 second
        time.sleep(1)
        # Get the drives plugged into the computer
        drives = get_mount_points()
        # For every drive
        for drive in drives:
            # If the drive has the searched for name
            if drive_name in drive[1]:
                # Log the drive as present
                drive_present = True
    # Print a log for the user
    print("Drive removed.\nProcess completed successfully!\n")
    # Print the new welcome message
    print("Please insert the drive to be copied...")
    # Return once the drive has been removed
    return "waitingForCopy"

# Create a folder witht he given name and copy the footage
def validateProjectName(project_name):
    return True

# While the program is running
while True:
    # If the program is waiting to copy footage
    if (state == "waitingForCopy"):
        # Check if it can copy and return the state
        state = checkCopy()
    # If the footage has been successfully copied
    elif (state == "copyComplete"):
        # Check if the drive has been removed
        state = waitRemove("Copy completed. Please remove the drive...")
    # If there wasn't enough space to copy
    elif (state == "notEnoughSpace"):
        # Inform the user there isn't enough space
        input("There is not enough space at the destination to copy. Press any key to continue...")
        # Check if it can copy and return the state
        state = checkCopy()
    # If there has been an error
    elif (state == "error"):
        # Wait for the drive to be removed
        state = waitRemove("Error occured. Please remove the drive...")
    # Wait for 5 seconds
    time.sleep(1)
