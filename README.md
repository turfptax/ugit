# ugit
Micropython OTA updates

load ugit.py into your ESP32 or any micropython internet enabled device
Change the user and repository variable to your github project

and this module will grab all of the files from the main branch and save them on your board

working on getting it to be able to delete files too but it is not finished.


USAGE:

#Change user variable and repository variable to your github information on ugit.py

import ugit

#connect to network somehow

ugit.pull_all_files()


