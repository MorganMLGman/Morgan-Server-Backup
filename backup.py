import os
from datetime import datetime
from time import mktime, time
import subprocess
import shutil

LOG_FILE_PATH = "/home/morgan/backup/backup.log"
BACKUP_DIR_PATH = "/home/morgan/DYSK/backups"
DIR_TO_BACKUP_PATH = "/home/morgan"
DIR_NAME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
BACKUP_DIR_NAME = BACKUP_DIR_PATH + "/" + DIR_NAME
DAYS_TO_KEEP = 7
SECONDS_IN_DAY = 86400
# 1 day = 86400 seconds
COMPRESS_BACKUP = True # True / False
DELETE_COMPRESSED = True # True / False

with open(LOG_FILE_PATH, 'a+') as LOG_FILE:
    for _ in range(75):
        LOG_FILE.write("=")
    LOG_FILE.write("\n")
    LOG_FILE.write(f"[{datetime.now()}] Starting backup script\n")
    
    os.chdir(BACKUP_DIR_PATH)
    LOG_FILE.write(f"[{datetime.now()}] Changing directory to: {BACKUP_DIR_PATH}\n")
    
    os.mkdir(DIR_NAME)
    LOG_FILE.write(f"[{datetime.now()}] Creating new direcory: {DIR_NAME}\n")
    
    LOG_FILE.write(f"[{datetime.now()}] Running `rsync -az --exclude-from='/home/morgan/backup/rsync-exclude.txt' --info=stats2 {DIR_TO_BACKUP_PATH} {BACKUP_DIR_NAME}`\n")
    rsync_out = subprocess.run(['rsync', '-az', '--exclude-from=\'/home/morgan/backup/rsync-exclude.txt\'', '--info=stats2', DIR_TO_BACKUP_PATH, BACKUP_DIR_NAME], stdout=subprocess.PIPE).stdout.decode('utf-8')
    
    for line in rsync_out.splitlines():
        LOG_FILE.write(f"\t{line}\n")
        
    LOG_FILE.write(f"[{datetime.now()}] Listing directory after running rsync\n")
    for item in os.listdir(BACKUP_DIR_PATH):
        LOG_FILE.write(f'\t{item}\n')
  
### GETING CONTENT OF A DIRECTORY ###
      
    dir_directories = next(os.walk(BACKUP_DIR_PATH), (None, [], None))[1]
    dir_files = next(os.walk(BACKUP_DIR_PATH), (None, None, []))[2]
    
### GETING OLD FILES AND DIRECTORIES ###

    LOG_FILE.write(f"[{datetime.now()}] Listing directories and files older then {DAYS_TO_KEEP} day(s)\n")
    
    old_directories = []
    old_files = []
    
    for item in dir_directories:
        if (mktime(datetime.strptime(item, "%Y-%m-%d %H:%M:%S").timetuple()) + DAYS_TO_KEEP * SECONDS_IN_DAY) < int(time()):
            old_directories.append(item)
            LOG_FILE.write(f"\tDirectory: {item}\n")
    
    for item in dir_files:
        item_tmp = item.replace(".tar.gz", "")
        if (mktime(datetime.strptime(item_tmp, "%Y-%m-%d %H:%M:%S").timetuple()) + DAYS_TO_KEEP * SECONDS_IN_DAY) < int(time()):
            old_files.append(item)
            LOG_FILE.write(f"\tFile: {item}\n")
      
    if not old_directories and not old_files:
        LOG_FILE.write(f"\tNo directories or files older then {DAYS_TO_KEEP} day(s)\n")
        
### DELETING OLD DIRECTORIES AND FILES ###

    if old_directories:
        LOG_FILE.write(f"[{datetime.now()}] Deleting old directories\n")        
        for item in old_directories:
            LOG_FILE.write(f"\tDeleting: {item}\n")
            shutil.rmtree(item)
    
    else:
        LOG_FILE.write(f"[{datetime.now()}] No old directories to delete\n")
        
    if old_files:
        LOG_FILE.write(f"[{datetime.now()}] Deleting old files\n")
        for item in old_files:
            LOG_FILE.write(f"\tDeleting: {item}\n")
            os.remove(item)
    else:
        LOG_FILE.write(f"[{datetime.now()}] No old files to delete\n")
        
### GETING CONTENT OF A DIRECTORY ###
      
    dir_directories = next(os.walk(BACKUP_DIR_PATH), (None, [], None))[1]
    dir_files = next(os.walk(BACKUP_DIR_PATH), (None, None, []))[2]
        

### COMPRESSING ###
        
    dir_to_compress = dir_directories        
    
    if COMPRESS_BACKUP:        
        if DIR_NAME in dir_to_compress: dir_to_compress.remove(DIR_NAME)
        
        LOG_FILE.write(f"[{datetime.now()}] Listing directories to compress\n")
        
        if dir_to_compress:
            for item in dir_to_compress:
                LOG_FILE.write(f"\t{item}\n")
            
            LOG_FILE.write(f"[{datetime.now()}] Compressing directories\n")
            
            for item in dir_to_compress:
                LOG_FILE.write(f"[{datetime.now()}] Compressing directory: {item}\n")
                shutil.make_archive(item, 'gztar', item)

### DELETING COMPRESSED DIRECTORIES ###            
            
            if DELETE_COMPRESSED:
                LOG_FILE.write(f"[{datetime.now()}] Deleting compressed directories\n")
                
                for item in dir_to_compress:
                    LOG_FILE.write(f"\tDeleting: {item}\n")
                    shutil.rmtree(item)
            
        else:
            LOG_FILE.write(f"\tNo directories to compress\n")
            
    LOG_FILE.write(f"[{datetime.now()}] Listing directory at the end of the script\n")
    for item in os.listdir(BACKUP_DIR_PATH):
        LOG_FILE.write(f'\t{item}\n')    
    
    LOG_FILE.write(f"[{datetime.now()}] End of backup script\n")