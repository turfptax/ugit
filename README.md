# ugit

#!!!!!!! DON'T USE UNTIL YOU HAVE TESTED ON A BOARD THAT DOESN'T HAVE CODE YOU HAVENT SAVED !!!!!!!!!!!!!

#Update: 12-15-2022

Bug0: It currently adds extra line breaks after downloading the files from github.

Bug1: It has a hard time navigating sub folders at the moment trying to fix

Bug2: Hash function not implemented because linebreaks mess up hash. It will always think there is an update

Requests: Any testors will make the process of debugging quicker.

Micropython OTA updates

load ugit.py and ugit_config.py into your ESP32 or any micropython internet enabled device
Change the user and repository variable to your github project

and this module will grab all of the files from the main branch and save them on your board
working on getting it to be able to delete files too but it is not finished.


#USAGE:

#Change user variable and repository variable to your github information on ugit.py

import ugit

#connect to network somehow

ugit.pull_all_files()

#TESTING:
import ugit

ugit.build_internal_tree()
# This is how it see's what is on the board and grabs the hash value of files
#Bug1 some none type errors occur trying to see if a folder is a directory sometimes gives none
# ugit.is_directory() is the check for this.
# Also belive there is a recursion error not sending the right full path in recursion.


