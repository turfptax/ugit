# ugit

# Micropython OTA Update Module
# Pulls github code from any public repository

# Micropython OTA updates
load ugit.py and ugit_config.py into your ESP32 or any micropython internet enabled device
Change the user and repository variable to your github project
and this module will grab all of the files from the main branch and save them on your board.

# USAGE:
Change user and repository variable to your github information on ugit_config.py

add files to ignore_files in ugit_config.py to ignore internal files from being overridden

code:

import ugit

!connect to network somehow

ugit.pull_all_files()

# TESTING:

import ugit

ugit.build_internal_tree() grabs internal file structure
ugit.pull(local_file_path,raw_file_url) pulls single raw files
ugit.pull_git_tree() pulls the github file tree from the repository
ugit.parse_git_tree() parses the github tree file to stdout
ugit.is_directory() checks if file path is a directory (folder).

# Things to note for developers:
Github requires a urequests header otherwise it will give you a 403 error.

Github uses main instead of master for URL api conncetion to repository tree. See source code in ugit.py for more informaiton.

  NOTE if you are pulling from a non-python repository you made need to change call_trees_url to /master? instead of /main? 
  
  giturl = 'https://github.com/{user}/{repository}'
  
  call_trees_url = f'https://api.github.com/repos/{user}/{repository}/git/trees/main?recursive=1'
 
  raw = f'https://raw.githubusercontent.com/{user}/{repository}/master/'

# Repository urepl is used to connect to the internet, it is another library i'm working on for UDP ascyncronus REPL. Check it out on github to learn more.
