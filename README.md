# ugit

# !!!!!!! TEST ON BOARD BEFORE DEPLOYMENT !!!

# Update: 12-16-2022
# Bug0:
It currently adds extra line breaks after downloading the files from github. This is an error with REPL environments from upycraft, Thonny view the data properly. There is still incorrect hash values calculated on the board. Am working on a fix using Githubs last hash value and saving in the config file instead of calculating the has on the micropython board.
# Bug1:
It has a hard time navigating sub folders at the moment trying to fix. 
	Subfolders that don't contain files cause error, fix needed.
# Bug2:
Hash function not implemented because it never matches up with github, see Bug0 for more details.
Requests: Any testors will make the process of debugging quicker.

# Micropython OTA updates
load ugit.py and ugit_config.py into your ESP32 or any micropython internet enabled device
Change the user and repository variable to your github project
and this module will grab all of the files from the main branch and save them on your board.

# USAGE:
# Change user variable and repository variable to your github information on ugit_config.py
import ugit
//connect to network somehow
ugit.pull_all_files()

# TESTING:
import ugit
ugit.build_internal_tree()
This is how it see's what is on the board and grabs the hash value of files
# ugit.is_directory() is the check for this.
# Also belive there is a recursion error not sending the right full path in recursion.

# Things to note for developers:
Github requires a urequests header otherwise it will give you a 4-3 error.
Github uses main instead of master for URL api conncetion to repository tree. See source code in ugit.py for more informaiton.

