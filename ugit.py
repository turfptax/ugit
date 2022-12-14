#ugit
# Get Github Updated micropython update

import os
import urequests
import urepl
import json

# CHANGE TO YOUR REPOSITORY INFO
# Also check out my friends amazing work
user = 'hwiguna'
repository = 'HariFun_208_Polymorph'

# Static URLS
# GitHub uses main instead of master for python repository trees
giturl = 'https://github.com/{user}/{repository}'
call_trees_url = f'https://api.github.com/repos/{user}/{repository}/git/trees/main?recursive=1'
raw = f'https://raw.githubusercontent.com/{user}/{repository}/master/'

def pull(f_path,giturl=giturl):
  #files = os.listdir()
  r = urequests.get(giturl)
  try:
    new_file = open(f_path, 'w')
    new_file.write(r.content.decode('utf-8'))
    new_file.close()
  except:
    print('decode fail try adding non-code files to .gitignore')
    try:
      new_file.close()
    except:
      print('tried to close new_file to save memory durring raw file decode')
  
def pull_all_files(tree=call_trees_url,raw = raw):
  r = urequests.get(tree,headers={'User-Agent': 'ugit-turfptax'})
  #^^^Requires user-agent header otherwise 403
  #print(r.content)
  tree = json.loads(r.content.decode('utf-8'))
  check = []
  # download and save all files
  for i in tree['tree']:
    if i['type'] == 'tree':
      try:
        os.mkdir(i['path'])
      except:
        print('failed to make directory may already exist')
    elif i['path'] != '.gitignore':
      try:
        os.remove(i['path'])
      except:
        print('failed to delete old file')
      pull(i['path'],raw + i['path'])
      try:
        check.append(i['path'])
      except:
        print('no slash or extension ok')
  # delete files not in tree
  return check

  

