
# ugit
# micropython OTA update from github
# Created by TURFPTAx for the openmuscle project
# Check out https://openmuscle.org for more info

import os
import urequests
import json
import hashlib
import machine
import time
import ugit_config

global internal_tree

# CHANGE TO YOUR REPOSITORY INFO
# Also check out my friends amazing work
user = ugit_config.user
repository = ugit_config.repository
ignore = ugit_config.ignore_files

# Static URLS
# GitHub uses main instead of master for python repository trees
giturl = 'https://github.com/{user}/{repository}'
call_trees_url = f'https://api.github.com/repos/{user}/{repository}/git/trees/main?recursive=1'
raw = f'https://raw.githubusercontent.com/{user}/{repository}/master/'

def pull(f_path,raw_url):
  print('pulls a single file from github')
  print('use like ugit.pull(file_path)')
  #files = os.listdir()
  r = urequests.get(raw_url)
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
  tree = pull_git_tree()
  check = []
  # download and save all files
  for i in tree['tree']:
    if i['type'] == 'tree':
      try:
        os.mkdir(i['path'])
      except:
        print('failed to make directory may already exist')
    elif i['path'] not in ugit_config.ignore_files:
      try:
        os.remove(i['path'])
      except:
        print('failed to delete old file')
      check_tree(i['path']) 
      try:
        pull(i['path'],raw + i['path'])
        check.append(i['path'] + ' updated')
      except:
        check.append(i['path'] + ' failed to pull')
  # delete files not in Github tree
  # Needs work :(
  logfile = open('ugit_log.py','w')
  logfile.write(str(check))
  logfile.close()
  time.sleep(10)
  machine.reset()
  #return check instead return with global

  
def build_internal_tree():
  global internal_tree
  internal_tree = []
  os.chdir('/')
  for i in os.listdir():
    add_to_tree(i)
  return(internal_tree)

def add_to_tree(dir_item):
  global internal_tree
  if is_directory(dir_item) and len(os.listdir(dir_item)) >= 1:
    os.chdir(dir_item)
    for i in os.listdir():
      add_to_tree(i)
    os.chdir('..')
  else:
    print(dir_item)
    if os.getcwd() != '/':
      subfile_path = os.getcwd() + '/' + dir_item
    else:
      subfile_path = os.getcwd() + dir_item
    try:
      print(f'sub_path: {subfile_path}')
      internal_tree.append([subfile_path,get_hash(subfile_path)])
    except OSError:
      print(f'{dir_item} could not be added to tree')

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
    return (os.stat(file)[8] == 0)
  except:
    return directory
    
def pull_git_tree(tree_url=call_trees_url,raw = raw):
  r = urequests.get(tree_url,headers={'User-Agent': 'ugit-turfptax'})
  # ^^^ Github Requires user-agent header otherwise 403
  tree = json.loads(r.content.decode('utf-8'))
  return(tree)
  
def parse_git_tree():
  tree = pull_tree()
  dirs = []
  files = []
  for i in tree['tree']:
    if i['type'] == 'tree':
      dirs.append(i['path'])
    if i['type'] == 'blob':
      files.append([i['path'],i['sha'],i['mode']])
  print('dirs:',dirs)
  print('files:',files)
   
