#ugit
# Get Github Updated micropython update

import os
import urequests
import urepl
import json

user = 'hwiguna'
repository = 'HariFun_166_Morphing_Clock'
giturl = 'https://github.com/{user}/{repository}'
call_trees_url = f'https://api.github.com/repos/{user}/{repository}/git/trees/master?recursive=1'

wlan = urepl.wificonnect()

def pull(f,giturl=giturl):
  #files = os.listdir()
  r = urequests.get(giturl)
  first_line = r.content.decode('utf-8').split('\n')[0]
  filename = giturl.split('/')[-1]
  new_file = open(filename, 'w')
  new_file.write(r.content.decode('utf-8'))
  #new_files = os.listdir()
  #added = list(set(new_files)-set(files))
  
def pull_all_files(tree=call_trees_url):
  r = urequests.get(tree,headers={'User-Agent': 'ugit-turfptax'})
  #^^^Requires user-agent header otherwise 403
  #print(r.content)
  tree = json.loads(r.content.decode('utf-8'))
  return tree

tree = pull_all_files()
for i in tree['tree']:
  print(i['path'])
  

