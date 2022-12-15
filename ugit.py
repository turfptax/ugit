#ugit
# Get Github Updated micropython update

import os
import urequests
import json
import hashlib
import machine
import time
import ugit_config

global tree

# CHANGE TO YOUR REPOSITORY INFO
# Also check out my friends amazing work
user = ugit_config.user
repository = ugit_config.repository

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
  os.chdir('/')
  internal_tree = build_internal_tree()
  # Github Requires user-agent header otherwise 403
  r = urequests.get(tree,headers={'User-Agent': 'ugit-turfptax'})
  # Turn Githubs tree into a python dict
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
      check_tree(i['path']) 
      pull(i['path'],raw + i['path'])
      try:
        check.append(i['path'] + ' updated')
      except:
        print('no slash or extension ok')
  # delete files not in Github tree
  # Needs work :(
  logfile = ('ugit_log.py','w')
  logfile.write(str(check))
  logfile.close()
  time.sleep(10)
  machine.reset()
  #return check instead return with global

  
def build_internal_tree():
  global tree
  tree = []
  os.chdir('/')
  for i in os.listdir():
    add_to_tree(i)
  return(tree)

def add_to_tree(f_path):
  global tree
  if is_directory(f_path):
    if len(os.listdir(f_path)) >= 1:
      print(f_path)
      os.chdir(f_path)
      folder = os.listdir(f_path)
      for i in folder:
        add_to_tree(i)
      os.chdir('..')
  else:
    print(f_path)
    if os.getcwd() != '/':
      subfile_path = os.getcwd() + '/' + f_path
    else:
      subfile_path = os.getcwd() + f_path
    try:
      tree.append([subfile_path,get_hash(subfile_path)])
    except OSError:
      print(f'{f_path} could not be added to tree')

def check_tree(file):
  global tree
  new_tree = []
  for i in tree:
    if i[0] == file:
      print(f'{file} found in tree')
    else:
      new_tree.append(i)
      print(f'{file} not in internal_tree')
  tree = new_tree
      
  
def get_hash(file):
  print(file)
  o_file = open(file)
  r_file = o_file.read()
  sha1obj = hashlib.sha1(r_file)
  hash = sha1obj.digest()
  return(hash.hex())
  
def is_directory(file):
  directory = False
  try:
    directory = (os.stat(file)[0] and os.stat(file)[7] == 0)
  except:
    return directory
  
  
