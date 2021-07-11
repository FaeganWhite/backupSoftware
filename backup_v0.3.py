
# Import packages
import time
import os
from glob import glob
from subprocess import check_output, CalledProcessError
from datetime import datetime, date
from distutils.dir_util import copy_tree
import shutil
from shutil import copytree
import sys
from shutil import copyfile
import traceback
import string
import asyncio
import smtplib, ssl


# CLASSES


# A folder object to hold information on footage folders
class Folder:
    # On creation
    def __init__(self, original_name, path, location):
        # Get the folder's original name
        self.original_name = original_name
        # Get the folder's path
        self.path = path
        # Get the folder's location
        self.location = location
        # Set the camera to None
        self.camera = "UNKNOWN_CAMERA"
        # Set the birth to None
        self.birth = None
    # Find its camera
    def findCamera(self):
        # Get the camera library 
        with open('camera_library.txt') as f:
            # Get each camera from the library
            cameras = [line.rstrip() for line in f]
        # Get all the xml files at the path
        xml_files = folderSearch('xml', self.path, False)
        # For each xml file
        for file in xml_files:
            # Open the xml file
            with open(file) as xml:
                # Get the data from the xml file
                data = xml.read()
                # For each camera
                for camera in cameras:
                    # If the camera's code is in the xml
                    if camera.split("-",1)[1].strip() in data:
                        # Save the camera
                        self.camera = camera.split("-",1)[0].strip()
    # Find its birth
    def findBirth(self):
        # Get the media types
        media_types = getMediaTypes()
        # For every footage type
        for media_type in media_types:
            # Find the first occurance
            media_files = folderSearch(media_type, self.path, False, True)
            # For each media file
            for media in media_files:
                # Set the folder's birth time to the creation date of the media file
                self.birth = os.path.getmtime(media)

# Class to store colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# SIMPLE ALGORITHMS


# Buble sort which sorts a list of objects according to a given attribute
def bubbleSort(sequence, sorting_property):
    # Get the number of objects
    n = len(sequence)
    # For each object
    for i in range(n-1):
        # Create a flag to check is sorted
        sorting = False
        # For each item
        for j in range(n-1):
            # If the attribute of the current object is larger than that of the following
            if getattr(sequence[j], sorting_property) > getattr(sequence[j+1], sorting_property):
                # Store the current object in a temporary variable
                tmp = sequence[j]
                # Swap the objects
                sequence[j] = sequence[j+1]
                # Swap the objects
                sequence[j+1] = tmp
                # Flag it's still sorting
                sorting = True
        # If the list is sorted
        if (sorting == False):
            # Break the loop
            break
    # Return the sorted list
    return sequence


# FILE PROCESSING FUNCTIONS


# Recursive function to get the size of a folder
def folderSize(path = '.'):
    # Get the total bytes
    total = 0
    # For every path
    for entry in os.scandir(path):
        # If it's a file
        if entry.is_file():
            # Add the filesize to the total size
            total += entry.stat().st_size
        # Otherwise if its a directory
        elif entry.is_dir():
            # If the folder isn't a hidden folder
            if (entry.name[0] != "."):
                # Add the size of the directory
                total += folderSize(entry.path)
    # Return the total
    return total

# Copy file tree from one destination to another
def recursiveCopy(origin_path, destination_path, total_amount, start_time, log_file, current_transfer_amount = 0, relative_path = ""):
    # For every path
    for entry in os.scandir(origin_path):
        # If it's a file
        if entry.is_file():
            # If the file doesn't already exist
            if (not os.path.isfile(os.path.join(os.path.join(destination_path, relative_path), entry.name))):
                # copy the file
                shutil.copy2(entry.path, os.path.join(os.path.join(destination_path, relative_path), entry.name))
                # Print to the log file
                printToLogFile(log_file, "COPEID: "+os.path.join(os.path.join(destination_path, relative_path), entry.name)+'\n')
            # Add the size of the file to the amount copied
            current_transfer_amount += os.path.getsize(entry.path)
            # Draw a loading bar
            drawLoadingBar(20, total_amount, current_transfer_amount, start_time)
        # Otherwise if its a directory
        elif entry.is_dir():
            # If the folder isn't a hidden folder
            if (entry.name[0] != "."):
                # If the folder doesn't already exist
                if (not os.path.isdir(os.path.join(os.path.join(destination_path, relative_path), entry.name))):
                    # Duplicate the folder
                    os.mkdir(os.path.join(destination_path, os.path.join(relative_path, entry.name)))
                    # Print to the log file
                    printToLogFile(log_file, "CREATED: "+os.path.join(destination_path, os.path.join(relative_path, entry.name))+'\n')
                # Add the size of the directory
                current_transfer_amount = recursiveCopy(entry.path, destination_path, total_amount, start_time, log_file, current_transfer_amount, os.path.join(relative_path, entry.name))
                # Draw a loading bar
                drawLoadingBar(20, total_amount, current_transfer_amount, start_time)
    # Return the total
    return current_transfer_amount

# Recursive function to search for files or folders
def folderSearch(search_term, path = '.', exact = True, first = False, folders_or_files=None):
    # create a list to return paths
    path_list = []
    # For every path
    for entry in os.scandir(path):
        # If the name matches the search term and it must be exact
        if (entry.name.lower() == search_term.lower() and exact == True):
            # If it's a file and the search isn't looking for folders or reverse
            if ((entry.is_file() and folders_or_files != "folders") or (entry.is_dir() and folders_or_files != "files")):
                # Add the path to the list of paths
                path_list.append(entry.path)
                # If only looking for the first
                if (first == True):
                    # return the path list
                    return path_list
        # Otherwise if the search term is in the name
        elif (search_term.lower() in entry.name.lower()):
            # If it's a file and the search isn't looking for folders or reverse
            if ((entry.is_file() and folders_or_files != "folders") or (entry.is_dir() and folders_or_files != "files")):
                # Add the path to the list of paths
                path_list.append(entry.path)
                # If only looking for the first
                if (first == True):
                    # return the path list
                    return path_list
        # If the entry is a directory
        if entry.is_dir():
            # Search the folder
            result = folderSearch(search_term, entry.path, exact)
            # Add the search of the folder
            path_list += result
            # If only looking for the first and something has been found
            if (first == True and len(result) > 0):
                # return the path list
                break
    # Return the list of directories
    return path_list

# Create a list of directories
def listFolders(path = '.', name=False):
    # List for directories
    total = []
    # For every path
    for entry in os.scandir(path):
        # If it's a directory
        if entry.is_dir():
            # Add the directory to the list
            total.append(entry.name)
    # Return the list
    return total

# Update the copying progress - called at each directory
def updateProgress(path, names):
    # Print the current directory
    print(path)
    # Ignore no file
    return []   

# Format data size
def formatDataSize(data):
    # If the value is between 0 and 1024
    if (0 <= data <= 1024):
        # Return Bytes
        return(str(round(data))+" B")
    # Otherwise divide dy 1024
    data = data/1024
    # If the value is between 0 and 1024
    if (0 <= data <= 1024):
        # Return Kilobyte
        return(str(round(data))+" KB")
    # Otherwise divide dy 1024
    data = data/1024
    # If the value is between 0 and 1024
    if (0 <= data <= 1024):
        # Return Megabyte
        return(str(round(data))+" MB")
    # Otherwise divide dy 1024
    data = data/1024
    # If the value is between 0 and 1024
    if (0 <= data <= 1024):
        # Return Gigabyte
        return(str(round(data))+" GB")
    # Otherwise divide dy 1024
    data = data/1024
    # If the value is between 0 and 1024
    if (0 <= data <= 1024):
        # Return Terabytes
        return(str(round(data))+" TB")
    # Otherwise divide dy 1024
    data = data/1024
    # Return Petabytes
    return(str(round(data))+" PB")

# Get the media types from the config file
def getMediaTypes():
    # Open the config file
    with open('config.txt') as f:
        # Get each line from the config
        lines = [line.rstrip() for line in f]
    # Get the media file types
    media_types = lines[0].split(":",1)[1].strip().split(",")
    # Strip any white space
    stripped_media_types = [s.strip() for s in media_types]
    # Return the media types
    return stripped_media_types

# Remove folders that don't contain any media
def cleanFolders(path):
    # Get the list of folders
    folders = listFolders(path)
    # Get the list of Media Types
    media_types = getMediaTypes()
    # for every folder
    for folder in folders:
        # Set a variable to see if it contains media
        contains_media = False
        # For each media type
        for type in media_types:
            # If a file of the type could be found
            if (folderSearch(type, os.path.join(path, folder), False, True) != []):
                # Save that the folder contains media
                contains_media = True
                # Break the loop
                break
        # If no media was found
        if (contains_media == False):
            # Change the permissions to allow removal
            os.chmod(os.path.join(path, folder), 0o777)
            # Delete the folder
            shutil.rmtree(os.path.join(path, folder))

# Print the loading bar
def drawLoadingBar(charNo, total, pos, start_time):
    # Return the cursor to the start of the line
    print("",end='\r')
    # Print the start of the loading bar
    print("Copying footage -> [", end='')
    # Calculate the number of blocks to draw in the loading bar
    amount = int(round(charNo*(pos/total)))
    # For every character required
    for a in range(amount):
        # Print a block
        print(u'\u2588', end='')
    # For every remaining character
    for a in range(charNo-amount):
        # Print a dash
        print('-', end='')
    # calculate the elapsed time
    elapsed = datetime.now() - start_time
    # If all the data hasn't been moved
    if (total != pos):
        # Calculate the estimated time
        estimated = ((datetime.now() - start_time)*total)/pos
    # Otherwise
    else:
        # Set the estimated time tot he elapsed time
        estimated = elapsed
    # Print the 
    print('] -> '+formatDataSize(pos)+" completed,  "+str(estimated-elapsed).split('.')[0]+" remaining          ", end='')

# Check if a project reference already exists
def checkRefExists(path, project_ref):
    # For every path
    for entry in os.scandir(path):
        # If it's a directory
        if entry.is_dir():
            # If the name contains the project reference number
            if (project_ref in entry.name):
                # Return a tuple with the name and path
                return (entry.name, entry.path)
    # otherwise return None
    return None

# Create a log file
def createLogFile(project_name, project_ref):
    # Generate a file name
    file_name = datetime.now().strftime("%y-%m-%d_%H-%M_%S_"+project_name+"_("+project_ref+")_LOG.txt")
    # Create and open the file
    log_file = open(os.path.join("logs",file_name), "w")
    # Wrte an opening line
    log_file.write("\n  *** "+project_name+" ("+project_ref+") - "+datetime.now().strftime("%d/%m/%y %H:%M:%S_"+"***\n\n"))
    # close file
    log_file.close()
    # Return the log file
    return os.path.join("logs",file_name)

# Print to a log file
def printToLogFile(log_file, message):
    # Open the log file
    file = open(log_file, 'a')
    # Add the folder name and size to the log file
    file.write(message)
    # Close the file
    file.close()


# VALIDATION FUNCTIONS


# Validate a provided project name
def validateProjectName(project_name):
    return True

# Validate a provided project reference
def validateProjectRef(project_ref):
    # If the length isn't 5
    if (len(project_ref) != 5):
        # Print error message
        print("Project reference must be 5 characters long!")
        # fail the function
        return False
    # For every character in the project reference
    for char in project_ref[:-1]:
        # If it isn't a number
        if not (char.isnumeric()):
            # Print that it must be a number
            print("The first 4 characters must be numbers")
            # Fail the reference
            return False
    # If the last character isn't a letter
    if not (project_ref[-1].isalpha()):
            # Print the last character must be a letter
            print("The last character must be a letter")
            # Fail the reference
            return False
    # Otherwise pass the reference
    return True

# Validate a provided project reference
def verifyCopy(drive_path, copy_path):
    return True

# Validate the config file
def validateConfig(lines):
    # Create a line counter
    if len(lines) < 4:
        # Fail the file
        return False
    # If the first line doesn't have media file types
    if (not 'MEDIA FILE TYPES:' in lines[0]):
        # Fail the config file
        return False
    # If the second line doesn't have media file types
    if (not 'DRIVE LOCATION:' in lines[1]):
        # Fail the config file
        return False
    # If the third line doesn't have primary copy location
    if (not 'PRIMARY COPY LOCATION:' in lines[2]):
        # Fail the config file
        return False
    # If the fourth line doesn't have secondary copy locations
    if (not 'SECONDARY COPY LOCATIONS:' in lines[3]):
        # Fail the config file
        return False
    # Otherwise pass the file
    return True

# Let the user double check their details
def doubleCheckDetails():
    # While true
    while True:
        # Double check details
        user_in = input("Are the above details correct? (y/n) ").strip().lower()
        # If details are not correct
        if (user_in == "n"):
            # go back to the start
            start()
        # else if details correct
        elif (user_in == "y"):
            # Continue
            return
        
# Let the user double check their details
def checkEmail():
    # While true
    while True:
        # Double check details
        user_in = input("Would you like email notifications? (y/n) ").strip().lower()
        # If details are not correct
        if (user_in == "n"):
            # return None
            return None
        # else if details correct
        elif (user_in == "y"):
            # Get the user's email address
            email = input("Please enter your email: ")
            # print message for user
            print("Emailing to",email,"once copying is completed")
            # Continue
            return email

# Let the user double check their details
def checkProxy():
    # While true
    while True:
        # check proxy
        user_in = input("Would you like to create video proxies after copying? (y/n) ").strip().lower()
        # If no proxy
        if (user_in == "n"):
            # return false
            return False
        # else if yes proxy
        elif (user_in == "y"):
            # Return true
            return True

# COMMUNICATION FUNCTIONS


# end an email to a given email address
def sendEmail(to_email, subject, message, from_email, password):
    # Select a port
    port = 465
    # Select a server
    smtp_server = "smtp.gmail.com"
    # Create a context
    context = ssl.create_default_context()
    # With the server
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        # Login using details
        server.login(from_email, password)
        # Send the email
        server.sendmail(from_email, to_email, 'Subject: {}\n\n{}'.format(subject, message))
    # Print an alert to the user
    print("Email notification sent")


# STATE FUNCTIONS


# Start the main function
def start():
    # Try 
    try:
        # Get the config file details
        with open('config.txt') as f:
            lines = [line.rstrip() for line in f]
        # If the config file is validated
        if validateConfig(lines):
            # Get the drive location
            drive_path = lines[1].split(":",1)[1].strip()
            # Get the copy location
            copy_path = lines[2].split(":",1)[1].strip()
            # Get the secondary copy locations
            secondary_paths = lines[3].split(":",1)[1].strip().split(",")
            # Strip any white space
            stripped_secondary_paths = [s.strip() for s in secondary_paths]
        # Otherwise
        else:
            # Exit the program
            exit("\nBackup's 'config.txt' is missing or missing information. Please amend and retry.")
    # If there's an error
    except Exception as error:
        # Exit the program
        exit("\n'Backup's config.txt' is missing or missing information. Please amend and restart retry.")
    # Try 
    try:
        # Print a title
        print(f"{bcolors.FAIL}\nAvailable drives: {bcolors.ENDC}")
        # Create a drive counter
        counter = 1
        # Get the drives
        drives = listFolders(drive_path)
        # For every drive
        for drive in drives:
            # Print the drive
            print(str(counter)+")",drive)
            # Increment the counter
            counter += 1
        # Give instructions for the user
        response = input("Please select a drive to digitise, (r)e-search or (e)xit: ").lower().strip()
        # If they want to rescan
        if (response == "r"):
            # Start the program from the start
            start()
        # Otherwise if they want to exit
        elif (response == "e"):
            # Print an exit messgae
            quit("Thank you for using Backup!")
        # If the response is a drive number
        elif (response.isnumeric()):
            # Round it and subtract 1
            drive_num = round(int(response))
            # If it corresponds to a drive
            if (int(response) <= len(drives)):
                # Print that the drive was found
                print("Digitising",os.path.join(drive_path,drives[drive_num-1]))
                # check if the drive can be copied
                checkCopy(os.path.join(drive_path,drives[drive_num-1]), copy_path, stripped_secondary_paths)
            # Otherwise
            else:
                # Print that the drive doesn't exist
                print("Drive '"+response+"' doesn't exist!")
                # Go back tot he start
                start()
        # Otherwise
        else:
            # Print that the command isn't recognised
            print("That command isn't recognised!")
            # Go back tot he start
            start()
    # If there's an error
    except Exception as error:
        # Handle the error
        handleError(error, "Start function", "")

# Check if a drive is there to be copied
def checkCopy(drive_path, copy_path, secondary_paths):
    # Try
    try:
        # Get the name of the project
        project_name = input("Enter a valid project name: ")
        # While the name isn't valid
        while not validateProjectName(project_name):
            # Get a new project name
            project_name = input("Enter the project name: ").strip()
        # Get the reference of the project
        project_ref = input("Enter the project reference: ").strip().upper()
        # While the reference isn't valid
        while not validateProjectRef(project_ref):
            # Get a new project name
            project_ref = input("Enter the project reference: ")
        # Search for footage with the same project reference
        check_reference = checkRefExists(copy_path, project_ref)
        # If one exists
        if (check_reference != None):
            # Ask the user if they would like to merge the project
            if (input("Project "+str(check_reference[0])+" already exists. Would you like to merge? (y/n) ").strip().lower() == "y"):
                # If so, copy the footage to the old path
                copyFootage(drive_path, copy_path, secondary_paths, project_name, project_ref, check_reference)
            else:
                # Otherwise try again
                checkCopy(drive_path, copy_path, secondary_paths)
        # Copy the footage and return the new state
        copyFootage(drive_path, copy_path, secondary_paths, project_name, project_ref)
    # If there's an error
    except Exception as error:
        # Handle the error
        handleError(error, project_name, project_ref)

# Create a folder with the given name and copy the footage
def copyFootage(drive_path, copy_path, secondary_paths, project_name, project_ref, merge=None):
    # try
    try:
        # Create an empty log file variable
        log_file = None
        # Create an empty email variable
        email = None
        # Unmask the os so that the copying results can be accessed by any user
        os.umask(0)
        # Get the values of the disk at the destination
        total, used, free = shutil.disk_usage(copy_path)
        # Print the space available in GB
        print("Space available: ", formatDataSize(free))
        # Get the size of the footage
        footage_size = folderSize(drive_path)
        # Print the size of the footage
        print("Footage size: ", formatDataSize(footage_size))
        # If there is enough space at the destination (with 10% extra space)
        if (free > footage_size*1.1):
            # Create a varibable to store whether ther is enough space in all the secondary destinations
            enough_secondary_space = True
            # Add the primary path as a tuple to the list of paths and their free space
            path_spaces = [(copy_path, free)]
            # For every secondary path
            for secondary_path in secondary_paths:
                # Get the amount of free space
                secondary_total, secondary_used, secondary_free = shutil.disk_usage(secondary_path)
                # Add the path and free space as a tuple
                path_spaces.append((secondary_path, secondary_free))
            # Create an outer counter to determine the place position in the path_spaces list
            outer_count = 0
            # For each path and space
            for path_space in path_spaces:
                # Create an inner counter to determine position in the list
                inner_count = 0
                # For every path and space
                for path_space_2 in path_spaces:
                    # If it isn't conparing against itself
                    if (outer_count != inner_count):
                        # If they have the same space and hence are the same drive
                        if (formatDataSize(path_space[1]) == formatDataSize(path_space_2[1])):
                            # Remove the second drive from the list
                            path_spaces.remove(path_space_2)
                            # Reduce the space of the first drive by the footage size to account for duplication
                            path_spaces[path_spaces.index(path_space)] = (path_space[0],path_space[1]-footage_size)
                    # Increment the inner counter
                    inner_count += 1
                # Increment the outer counter
                outer_count = 1
            # For every path and space pair remaining
            for path_space in path_spaces:
                # Compare the free space against the footage size
                if (path_space[1] < footage_size*1.1):
                    # Save the drive that is full
                    full_drive = path_space
                    # If there isn't enough free space, set the value
                    enough_secondary_space = False
                    # Break the loop
                    break
            # If there isn't enough free space on one of the drives
            if (enough_secondary_space == False):
                # Print that there wasn't enough space
                handleError("Not enough space to duplicate to "+full_drive[0]+". Requires "+formatDataSize((footage_size*1.1)-full_drive[1])+" more space!", project_name, project_ref, email, log_file)
            # Create a file counter
            file_count = 0
            # For each file
            for root, dirs, files in os.walk(drive_path):
                # Increment the number of files
                file_count += len(files)
                # Increment the number of directories
                file_count += len(dirs)
            # Print the number of files
            print("Number of files to copy: ",file_count)
            # If the project doen't already exist
            if (merge == None):
                # Create a new path using the project name and reference
                new_path = os.path.expanduser(os.path.join(copy_path,project_name+" ("+project_ref+")"))
                # Make the project directory
                os.mkdir(new_path)
            else:
                # Otherwise get the path of the already existing file
                new_path = merge[1]
                # Get the new project name
                project_name = merge[0].split(" (")[len(merge[0].split(" ("))-2]
            # Print that the footage is being copied
            print("Copying to", new_path)
            # Get the users email address
            email = checkEmail()
            # Get the users proxy decision
            proxy = checkProxy()
            # Double check the details are correct
            doubleCheckDetails()
            # Store the number of folders
            number_of_folders = len(listFolders(new_path))
            # Create the log file
            log_file = createLogFile(project_name, project_ref)
            # Copy the contents from the drive to the provided location
            recursiveCopy(drive_path, new_path, footage_size, datetime.now(), log_file)
            # If the footage was successfully copied
            if verifyCopy(drive_path, new_path):
                # Rename the folders at the main path
                renameFolders(new_path, project_name, project_ref)
                # Print to the log file
                printToLogFile(log_file, "\n"+str(len(listFolders(new_path))-number_of_folders)+" folders have been copied to "+new_path+"\n("+str(len(listFolders(new_path)))+" total)\n")
                # For every file at the location
                for location in listFolders(new_path):
                    # Print to the log file
                    printToLogFile(log_file,"- "+location+" "+formatDataSize(folderSize(os.path.join(new_path, location)))+'\n')
                # Print to the log file
                printToLogFile(log_file,'\n')
                # Print the number of folders
                print("\n"+str(len(listFolders(new_path))-number_of_folders),"folders have been copied to",new_path," ("+str(len(listFolders(new_path)))+" total)")
                # Alert the user the folders have been renamed
                print("Folders renamed")
                # Rename the folders at the main path
                renameFootage(new_path)
                # For every second path
                for secondary_path in secondary_paths:
                    # Print to the log file
                    printToLogFile(log_file,"Duplicating the footage to "+os.path.join(secondary_path,project_name+" ("+project_ref+")\n\n"))
                    # Print that the footage is being duplicated
                    print("Duplicating the footage to",os.path.join(secondary_path,project_name+" ("+project_ref+")"))
                    # If the folder doesn't exist
                    if not os.path.isdir(os.path.join(secondary_path,project_name+" ("+project_ref+")")):
                        # Make the project directory
                        os.mkdir(os.path.join(secondary_path,project_name+" ("+project_ref+")"))
                        # Print to the log file
                        printToLogFile(log_file, os.path.join(secondary_path,project_name+" ("+project_ref+")")+'\n')
                    # Copy the contents from the drive to the provided location
                    recursiveCopy(new_path, os.path.join(secondary_path,project_name+" ("+project_ref+")"), folderSize(new_path), datetime.now(), log_file)
                    # Print a message to the user
                    print("\nDuplication successful")
                    # Print to the log file
                    printToLogFile(log_file, "\nAll footage transferred successfully.")
                # Return a success
                finishedCopying(email, project_name, project_ref, log_file)
            else:
                # Handle a failed copy
                handleCopyFail()

        else:
            # Print that there wasn't enough space
            handleError("Not enough space at location "+copy_path+". Requires "+formatDataSize((footage_size*1.1)-free)+" more space!", project_name, project_ref, log_file)
     # If there's an error
    except Exception as error:
        # Handle the error
        handleError(error, project_name, project_ref, log_file, email)

# Rename folders at a location
def renameFolders(path, project_name, project_ref):
    # Remove any folders without media
    cleanFolders(path)
    # Get the number of folders
    folders = listFolders(path)
    # Create a list of folder objects
    folder_objects = []
    # For each folder
    for folder in folders:
        # Create a folder object with the name and path
        new_folder = Folder(folder, os.path.join(path, folder), path)
        # Find each folder's camera
        new_folder.findCamera()
        # Find each folder's birth
        new_folder.findBirth()
        # Add the folder object to the list
        folder_objects.append(new_folder)
    # Create a list to classify folders by camera
    folders_by_camera = []
    # For each folder object
    for folder in folder_objects:
        # Store the position in the camera class list
        position = 0
        # For each camera type
        for camera_class in folders_by_camera:
            # First folder in this type has the same camera
            if (camera_class[0].camera == folder.camera):
                 # Add the camera
                 camera_class.append(folder)
                 # break the loop
                 break
            else:
                # Otherwise increment the position in the list of camera classes
                position += 1
        # If position is the same as the length aka. there was no folder recorded witht he same camera type
        if (position == len(folders_by_camera)):
            # Create a new list for camera tpes with the current folder at the top
            new_camera_class = [folder]
            # Add this new list to the total list of camera type folders
            folders_by_camera.append(new_camera_class)
    # Create a new list to hold folders sorted by date created
    sorted_folders_by_camera = []
    # For each camera type
    for camera_class in folders_by_camera:
        # Sort the folders according to their birth
        sorted_class = bubbleSort(camera_class, "birth")
        # Add the sorted_folders to the list of
        sorted_folders_by_camera.append(sorted_class)
    # For each list of sorted folders
    for sorted in sorted_folders_by_camera:
        # Start the counter at 1
        counter = 1
        # For each folder with the same camera type
        for folder in sorted:
            # Rename the folder using the given details
            os.rename(folder.path, os.path.join(folder.location,folder.camera+"_"+str(counter)+"_"+str(datetime.fromtimestamp(folder.birth).strftime('%Y-%m-%d'))+"_"+project_ref+"_"+project_name.translate(str.maketrans('', '', string.punctuation))))
            # Increment the counter
            counter += 1

# Rename all the footage that has been copied
def renameFootage(path):
    # Get a list of all the folders
    folders = listFolders(path)
    # For every folder
    for folder in folders:
        # Get the list of Media Types
        media_types = getMediaTypes()
        # Create a list to hold media files
        media_files = []
        # For each media type
        for type in media_types:
            # Find the media files in the folder and add them to the list of media files
            media_files += folderSearch(type, os.path.join(path, folder), False, False, "files")
        # Get a list of all the XML files
        xml_files = folderSearch("XML", os.path.join(path, folder), False, False, "files")
        # Create a list to hold xml files in the same directories as media files
        media_linked_xml_files = []
        # For every XML file
        for xml in xml_files:
            # Set media in the smae dirctory as false
            media_linked = False
            # For every media file
            for media in media_files:
                # If they have the same directory
                if (media[:media.rfind('/')] == xml[:xml.rfind('/')]):
                    # set linked to true
                    media_linked = True
                    # Break the loop
                    break
            # If the xml file is media linked
            if media_linked:
                # Add it to the the list of linked xml files
                media_linked_xml_files.append(xml)
        # Add together the list of media and linked XML files
        all_files = media_files + media_linked_xml_files
        # For every file
        for file in all_files:
            # Split the folder name
            sections = folder.split("_")
            # Get the number of sections
            n = len(sections)
            # Get a new file name
            new_path = file[:file.rfind('/')]+"/"+sections[n-5].split("/")[len(sections[n-5].split("/"))-1]+"_"+sections[n-4]+"_"+sections[n-2]+"_"+file[file.rfind('/')+1:]
            # Rename the file
            os.rename(file, new_path)
    # Alert the user the footage has been renamed
    print("Footage renamed")

# Pause until the drive has been removed
def finishedCopying(email, project_name, project_ref, log_file):
    # if the user gave an email address
    if (email != None):
        # Try
        try:
            # Send an email
            sendEmail(email, 'Footage transfer successful', project_name+" ("+project_ref+") was successfully transfered to all locations.\nYou may remove the drive from the machine.", 'richbackupnotification@gmail.com', "s8XSQ'Y>P7uh8UX*")
         # If there's an error
        except Exception as error: 
            # Handle the error
            handleError(error, project_name, project_ref, log_file, None, True)
    # Check if the user wants to digitise again
    check_quit = input("Do you want to digitise again? (y/n) ")
    # If the user wants to digitise again
    if (check_quit.lower().strip() == "y"):
        # Start again
        start()
    # Otherwise
    else:
        # Quit the program
        quit("Thank you for digitising with Backup!")

# Quit the program
def quit(message):
    # Print an exit message
    print(message+"\n")
    # Quit the program
    sys.exit()


# HANDLING ERRORS


# Function to handle error
def handleError(error, project_name, project_ref, log_file = None, email = None, override = False):
    # Open the error log file
    with open('error_log.txt', 'a') as the_file:
        # Get the date and time
        now = datetime.now()
        # Add the date and the error to the log
        the_file.write("\n"+now.strftime("%m/%d/%Y, %H:%M:%S")+" - "+project_name+" ("+project_ref+')\n'+str(traceback.format_exc())+'\n'+str(error)+'\n')
    # If there's a log file
    if (log_file != None):
        # Print the error to the log file
        printToLogFile(log_file, "\n"+now.strftime("%y/%m/%d, %H:%M:%S")+'\n'+str(traceback.format_exc())+'\n'+str(error)+'\n\n')
    # If there is a traceback
    if ("NoneType: None" not in traceback.format_exc() and not override):
        # Print the traceback
        print(traceback.format_exc())
    # Otherwise
    else:
        # Print the error provided
        print(error)
    # if the user gave an email address
    if (email != None):
        # Try
        try:
            # Send an email
            sendEmail(email, 'Error during footage transfer', project_name+" ("+project_ref+") may have failed to transfer to all locations due to an error.\nYou may remove the drive from the machine or attempt to digitise again.\n\nError: \n"+now.strftime("%m/%d/%Y, %H:%M:%S")+" - "+project_name+" ("+project_ref+')\n'+str(traceback.format_exc())+'\n'+str(error)+'\n', 'richbackupnotification@gmail.com', "s8XSQ'Y>P7uh8UX*")
         # If there's an error
        except Exception as error: 
            # Handle the error
            print("Attempt to email error to",email,"has failed.")
    # Check if the user wants to digitise again
    check_quit = input("Do you want to try again? (y/n) ")
    # If the user wants to digitise again
    if (check_quit.lower().strip() == "y"):
        # Go back to the start
        start()
    # Otherwise
    else:
        # Quit
        quit("Exiting Backup...")

def handleCopyFail():
    print("FOOTAGE HASN'T BEEN FULLY COPIED!")


# MAIN LOOP

# Start the program
start()