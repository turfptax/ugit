#ugit
# Get Github Updated micropython update

import os
import urequests
import json
import hashlib

# CHANGE TO YOUR REPOSITORY INFO
# Also check out my friends amazing work
user = 'turfptax'
repository = 'ugit_test'

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

  
def build_internal_tree():
  tree = []
  os.chdir('/')
  for i in os.listdir():
    try:
      folder = os.listdir(i)
    except:
      folder = False
    if not folder:
      file_path = os.getcwd() + i
      tree.append([file_path,get_hash(file_path)])
    else:
      os.chdir(i)
      for x in folder:
        subfile_path = os.getcwd()+'/' +x
        tree.append([subfile_path,get_hash(subfile_path)])
      os.chdir('..')
  return(tree)
  
def get_hash(file):
  o_file = open(file)
  r_file = o_file.read()
  sha1obj = hashlib.sha1(r_file)
  hash = sha1obj.digest()
  return(hash.hex())
  
