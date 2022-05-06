import os
from colorama import Fore
from datetime import datetime
from time import mktime, time
import subprocess
import shutil
import argparse

TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"

PERMISSION_USER = 1000
PERMISSION_GROUP = 1000

LOG_FILE_PATH = "/home/morgan/backup/backup.log"
BACKUP_DIR_PATH = "/home/morgan/DYSK/backups"
BACKUP_DIR_NAME = "current"

EXCLUDE_FILE = "/home/morgan/backup/rsync-exclude.txt"

EXTERNAL_DRIVE_MOUNT_POINT = "/home/morgan/DYSK"

DIR_TO_BACKUP_PATH = "/home/morgan"
BACKUP_NAME = datetime.now().strftime(TIME_FORMAT)

CREATE_COPY = True # Will create a copy or archive of a backup directory each time script is run
COMPRESS_BACKUP = True # Compress backups after syncing or not
COMPRESSION_FORMAT = "bztar" # gztar or zip, bztar
DELETE_OLD = True # Delete old compressed backups or not

DAYS_TO_KEEP = 7
SECONDS_IN_DAY = 86400

class LOG:    
    logFile = ""
    mode = "po"
    
    def __init__(self, mode: str) -> None:        
        match mode:
            case "fo":
                self.mode = mode            
            case "fap":
                self.mode = mode            
            case "po":
                self.mode = mode            
            case "none":
                self.mode = mode        
            case _:
                self.mode = "po"
        
    def set_log_file(self, logFile: str) ->None:
        """Set logging file and create it if don't exists

        Args:
            logFile (str): Absolute file path
        """
        with open(logFile, "a+") as file:
            if self.mode == "fap" or self.mode == "fo":
                for _ in range(100):
                    file.write("=")
                file.write("\n\n")
                       
        self.logFile = logFile
    
    def set_mode(self, mode: str) -> bool:
        """Set logging mode: "fo" - file only, "fap" - file and print, "po" - print only, "none" - none

        Args:
            mode (str): logging mode

        Returns:
            bool: True if success else False
        """
        match mode:
            case "fo":
                if self.logFile != "":
                    self.mode = mode            
                    return True
                else: 
                    return False
            case "fap":
                if self.logFile != "":
                    self.mode = mode            
                    return True
                else: 
                    return False         
            case "po":
                self.mode = mode
                return True        
            case "none":
                self.mode = mode
                return True     
            case _:
                self.mode = "po"
                return True
    
    def get_log_size(self) -> float:
        """Get log file size

        Returns:
            float: file size in kilobytes
        """
        if self.logFile != "" and os.path.exists(self.logFile):
            return round(os.path.getsize(self.logFile) / 1024.0, 2)
        else:
            return 0

    def __check_logfile_path(self) -> bool:
        """Check if path to logfile is valid

        Returns:
            bool: True if valid
        """
        if "" != self.logFile and os.path.exists(self.logFile):
            return True
        else:
            return False        
        
    def __write_to_file(self, text: str, timestamp: str) -> None:
        """Private function writting logs to file

        Args:
            text (str): Text to log
        """
        
        if ("fap" == self.mode or "fo" == self.mode) and "" != text and self.__check_logfile_path():
            with open(self.logFile, "a+") as file:
                if len(text.splitlines()) > 1:
                    file.write(f"[{timestamp}]\n")
                    for line in text.splitlines():
                        file.write(f"\t{line}\n")
                else:
                    file.write(f"[{timestamp}] {text}\n")
        
    def write(self, text: str) -> None:
        """Log text according to set mode

        Args:
            text (str): Text to log
        """
        
        timestamp = datetime.now()
        
        match self.mode:
            case "fap":
                if len(text.splitlines()) > 1:
                    print(f"[{timestamp}]")
                    for line in text.splitlines():
                        print(f"\t{line}")
                else:
                    print(f"[{timestamp}] {text}")
                self.__write_to_file(text, timestamp)
            case "fo":
                self.__write_to_file(text, timestamp)
            case "po":
                if len(text.splitlines()) > 1:
                    print(f"[{timestamp}]")
                    for line in text.splitlines():
                        print(f"\t{line}")
                else:
                    print(f"[{timestamp}] {text}")
            case _:
                pass # same as none, nothing to do
        
def get_dir_size(path=DIR_TO_BACKUP_PATH):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir() and entry.path != EXTERNAL_DRIVE_MOUNT_POINT:
                total += get_dir_size(entry.path)
    return total 

parser = argparse.ArgumentParser(description="Backup script", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--dry-run", action="store_true", help="Run script with dry run option, useful to check config without modifying anything")
args = parser.parse_args()
config = vars(args)

if os.getuid() == 0 and os.getgid() == 0:
    log = LOG("fap")
    log.set_log_file(LOG_FILE_PATH)
    log.write("Starting backup script as root")
    log.write(f"Changing directory to: {BACKUP_DIR_PATH}")
    
    os.chdir(BACKUP_DIR_PATH)
    
    log.write(f"Checking if external drive is mounted.\nAvailable space at {BACKUP_DIR_PATH} greater than\nspace available at \'/\' will indicate that the drive is mounted.")
    
    root_total, root_used, root_free = shutil.disk_usage("/")    
    mount_total, mount_used, mount_free = shutil.disk_usage(BACKUP_DIR_PATH)
    
    if not mount_total > root_total:
        log.write(f"External drive is not mounted\n\nEnd of backup script")
        exit()
    else:
        log.write(f"Safe to proceed, external drive is mounted.\nSpace available at external drive is: {round(mount_free / (2**30), 2)} GiB")

    log.write(f"Check if available space at external drive is enough to create new backup")
    
    dir_size = round (get_dir_size() / (2**30), 2)
    
    if not mount_used > dir_size * 2.0:
        log.write(f"Available space is not enough to create another backup.\n\
Free space at external drive: {round(mount_free / (2**30), 2)} GiB\n\
Size of directory to backup is: {dir_size} GiB\n\
To be on the safe side double the space is required\n\n\
End of backup script")
        exit()
    else:
        log.write(f"\
Available space is enough to create another backup.\n\
Free space at external drive: {round(mount_free / (2**30), 2)} GiB\n\
Size of directory to backup is: {dir_size} GiB")
        
    if not config["dry_run"]:
        log.write(f"Running `rsync -az --delete --exclude-from={EXCLUDE_FILE} --info=stats2 {DIR_TO_BACKUP_PATH} {BACKUP_DIR_PATH}/{BACKUP_DIR_NAME}")
        rsync_out = subprocess.run(['rsync', '-az', '--delete', f"--exclude-from={EXCLUDE_FILE}", '--info=stats2', DIR_TO_BACKUP_PATH, f"{BACKUP_DIR_PATH}/{BACKUP_DIR_NAME}"], stdout=subprocess.PIPE).stdout.decode('utf-8')
    else:
        log.write(f"Running `rsync -az --dry-run --delete --exclude-from={EXCLUDE_FILE} --info=stats2 {DIR_TO_BACKUP_PATH} {BACKUP_DIR_PATH}/{BACKUP_DIR_NAME}")
        rsync_out = subprocess.run(['rsync', '-az', '--dry-run', '--delete', f"--exclude-from={EXCLUDE_FILE}", '--info=stats2', DIR_TO_BACKUP_PATH, f"{BACKUP_DIR_PATH}/{BACKUP_DIR_NAME}"], stdout=subprocess.PIPE).stdout.decode('utf-8')
    log.write(rsync_out)
    
    if CREATE_COPY:    
        if COMPRESS_BACKUP:
            log.write(f"Compressing backup directory to {COMPRESSION_FORMAT} archive")
            start_time = time()
            if not config["dry_run"]:            
                shutil.make_archive(BACKUP_NAME, COMPRESSION_FORMAT, f"{BACKUP_DIR_PATH}/{BACKUP_DIR_NAME}")
                log.write(f"Compression took {time() - start_time} seconds")
                log.write(f"Settings archive permissions USER:{PERMISSION_USER}, GROUP:{PERMISSION_GROUP}")
                shutil.chown(f"{BACKUP_DIR_PATH}/{BACKUP_NAME}", user=PERMISSION_USER, group=PERMISSION_GROUP)
            else:
                log.write(f"Here compression take place, but --dry-run is enabled so only a placeholder")
            log.write(f"Compression took {round(time() - start_time, 2)} seconds")
            
        else:
            log.write(f"Creating copy of a {BACKUP_DIR_NAME} directory to a {BACKUP_NAME} directory")
            start_time = time()
            if not config["dry_run"]:
                shutil.copytree(f"{BACKUP_DIR_PATH}/{BACKUP_DIR_NAME}", f"{BACKUP_DIR_PATH}/{BACKUP_NAME}", symlinks=True)
                log.write(f"Settings directory permissions USER:{PERMISSION_USER}, GROUP:{PERMISSION_GROUP}")
                chown_out = subprocess.run(["chown", "-R", f"{PERMISSION_USER}:{PERMISSION_GROUP}", f"{BACKUP_DIR_PATH}/{BACKUP_NAME}"], stdout=subprocess.PIPE).stdout.decode('utf-8')
                log.write(chown_out)
            else:
                log.write(f"Here copy take place, but --dry-run is enabled so only a placeholder")                
            log.write(f"Copying took {round(time() - start_time, 2)} seconds")
            
    if DELETE_OLD:
        log.write(f"Deleting archives older than {DAYS_TO_KEEP} days")
        log.write(f"Listing directory {BACKUP_DIR_PATH} before deleting")
        
        dir_directories = next(os.walk(BACKUP_DIR_PATH), (None, [], None))[1]
        dir_files = next(os.walk(BACKUP_DIR_PATH), (None, None, []))[2]
        
        text = "\n\t".join(item for item in dir_directories)        
        log.write(f"Directory list:\n\t{text}")
        text = "\n\t".join(item for item in dir_files) 
        log.write(f"File list:\n\t{text}")
                
        dir_directories.pop(dir_directories.index(BACKUP_DIR_NAME))
        
        old_directories = []
        old_files = []
        
        for item in dir_directories:
            if (mktime(datetime.strptime(item, TIME_FORMAT).timetuple()) + DAYS_TO_KEEP * SECONDS_IN_DAY) < int(time()):
                old_directories.append(item)
                
        for item in dir_files:
            if (mktime(datetime.strptime(item.split(".")[0], TIME_FORMAT).timetuple()) + DAYS_TO_KEEP * SECONDS_IN_DAY) < int(time()):
                old_files.append(item)
                
        log.write(f"Listing items that would be deleted:")
        text = "\n\t".join(item for item in old_directories)        
        log.write(f"Directory list:\n\t{text}")
        text = "\n\t".join(item for item in old_files) 
        log.write(f"File list:\n\t{text}")
else:
    print(f"\n\t{Fore.RED}Sorry but running this script without root permissions won't create full backup.{Fore.RESET}\n")

# with open(LOG_FILE_PATH, 'a+') as LOG_FILE:
#     for _ in range(75):
#         LOG_FILE.write("=")
#     LOG_FILE.write("\n")
#     LOG_FILE.write(f"[{datetime.now()}] Starting backup script\n")
    
#     os.chdir(BACKUP_DIR_PATH)
#     LOG_FILE.write(f"[{datetime.now()}] Changing directory to: {BACKUP_DIR_PATH}\n")
    
#     LOG_FILE.write(f"[{datetime.now()}] Running `rsync -az --exclude-from='/home/morgan/backup/rsync-exclude.txt' --info=stats2 {DIR_TO_BACKUP_PATH} {BACKUP_DIR_NAME}`\n")
#     rsync_out = subprocess.run(['rsync', '-az', '--exclude-from=/home/morgan/backup/rsync-exclude.txt', '--info=stats2', DIR_TO_BACKUP_PATH, BACKUP_DIR_NAME], stdout=subprocess.PIPE).stdout.decode('utf-8')
    
#     for line in rsync_out.splitlines():
#         LOG_FILE.write(f"\t{line}\n")
        
#     LOG_FILE.write(f"[{datetime.now()}] Listing directory after running rsync\n")
#     for item in os.listdir(BACKUP_DIR_PATH):
#         LOG_FILE.write(f'\t{item}\n')
  
# ### GETING CONTENT OF A DIRECTORY ###
      
#     dir_directories = next(os.walk(BACKUP_DIR_PATH), (None, [], None))[1]
#     dir_files = next(os.walk(BACKUP_DIR_PATH), (None, None, []))[2]
    
# ### GETING OLD FILES AND DIRECTORIES ###

#     LOG_FILE.write(f"[{datetime.now()}] Listing directories and files older then {DAYS_TO_KEEP} day(s)\n")
    
#     old_directories = []
#     old_files = []
    
#     for item in dir_directories:
#         if item == "current":
#             continue
            
#         if (mktime(datetime.strptime(item, "%Y-%m-%d_%H-%M-%S").timetuple()) + DAYS_TO_KEEP * SECONDS_IN_DAY) < int(time()):
#             old_directories.append(item)
#             LOG_FILE.write(f"\tDirectory: {item}\n")
    
#     for item in dir_files:
#         item_tmp = item.replace(".tar.gz", "")
#         if (mktime(datetime.strptime(item_tmp, "%Y-%m-%d_%H-%M-%S").timetuple()) + DAYS_TO_KEEP * SECONDS_IN_DAY) < int(time()):
#             old_files.append(item)
#             LOG_FILE.write(f"\tFile: {item}\n")
      
#     if not old_directories and not old_files:
#         LOG_FILE.write(f"\tNo directories or files older then {DAYS_TO_KEEP} day(s)\n")
        
# ### DELETING OLD DIRECTORIES AND FILES ###

#     if old_directories:
#         LOG_FILE.write(f"[{datetime.now()}] Deleting old directories\n")        
#         for item in old_directories:
#             LOG_FILE.write(f"\tDeleting: {item}\n")
#             shutil.rmtree(item)
    
#     else:
#         LOG_FILE.write(f"[{datetime.now()}] No old directories to delete\n")
        
#     if old_files:
#         LOG_FILE.write(f"[{datetime.now()}] Deleting old files\n")
#         for item in old_files:
#             LOG_FILE.write(f"\tDeleting: {item}\n")
#             os.remove(item)
#     else:
#         LOG_FILE.write(f"[{datetime.now()}] No old files to delete\n")

# ### COMPRESSING ###
        
#     #dir_to_compress = dir_directories.pop("current")        
#     dir_to_compress = "current"
    
#     if COMPRESS_BACKUP:
#         LOG_FILE.write(f"[{datetime.now()}] Compressing directory: {dir_to_compress}\n")
#         shutil.make_archive(BACKUP_TAR_NAME, 'gztar', BACKUP_DIR_NAME)
            
#     LOG_FILE.write(f"[{datetime.now()}] Listing directory at the end of the script\n")
#     for item in os.listdir(BACKUP_DIR_PATH):
#         LOG_FILE.write(f'\t{item}\n')    
    
#     LOG_FILE.write(f"[{datetime.now()}] End of backup script\n")