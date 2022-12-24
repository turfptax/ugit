<br />
<div align="center">
    <img src="images/ugit_ugit-main-image.jpg" alt="Logo" width="100%">
    <h1 align="center">Micropython OTA Updates</h1>
  <h3 align="center">Keep your remote ESP32 devices in sync with a github repo.</h3>
  <h2 align="center">Pulls entire github repository onto a micropython board</h2>
  <p align="center"> Over The Air, with one command: ugit.pull_all()</p>
</div>


## About ugit

This is meant to clone an entire micropython repository to an internet enable micropython microcontroller. You can use it to periodically update the entire ESP32 micropython file structure to match an open github repository.

If there are files that you want to be left intact on the ESP32 regardless of the changes done to the github repository. Just add the file name in ignore_files array. Located on line 27 of ugit.py.

ugit functions:
* ugit will update the internal file structure of an ESP32 with a github repository
* Files Folders and file Deletions are updated to the board
* Specify which repository, ingore files, and user inside of ugit.py

<img src="images/ugit_screenshot.png" alt="Logo" width="600" height="600">

With ugit you can update a micropython board with a complete micropython library from github.

Download `ugit.py` to your ESP32 micropython board to get started.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<img src="images/ugit_ugit-divider.png" alt="Logo"  height="20">
<!-- GETTING STARTED -->

# make sure to back up your code before trying ugit
## when you run ugit.pull_all() it will download all the files in the repository and delete any files on the board that are not in the variable ignore_files array.

## Getting Started

```python
#boot.py

import ugit

ugit.backup() # good idea to backup your files!

ugit.pull_all()
```
### Installation

Simply put: copy ugit.py onto the micropython board.

1. Copy ugit.py onto your micropython board
2. modify ugit_config with the user,repository,ssid, and password
4. run the ugit.pull_all()

<img src="images/ugit_ugit-divider.png" alt="Logo"  height="20">
<!-- USAGE EXAMPLES -->
## Usage

You can use ugit without any other code in boot. It will connect to wifi and download filetree from github and copy the raw data to your board.

```python
# boot.py

import ugit

ugit.pull_all()
```

### If you want to use your own method of connecting to wifi you can add the isconnected=true parameter to ugit.pull_all()

```python
#boot.py
    
import ugit

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SSID','Password')

ugit.pull_all(isconnected=True)
```

### You can also use the built in function wificonnect()
```python
import ugit

wlan = ugit.wificonnect('SSID','PASSWORD')

# backup internal files
ugit.backup() # saves to ugit.backup file

# Pull single file
ugit.pull('file_name.ext','Raw_github_url')

# backup board's files
ugit.backup()

# Pull all files
ugit.pull_all()
```

<img src="images/ugit_ugit-divider.png" alt="Logo"  height="20">
### TESTING:

We plan to include a roll-back feature in the future where you can roll back to a previous state.

```python
import ugit

ugit.build_internal_tree() #grabs internal file structure
ugit.pull(local_file_path,raw_file_url) #pulls single raw files
ugit.pull_git_tree() #pulls the github file tree from the repository
ugit.parse_git_tree() #parses the github tree file to stdout
ugit.is_directory() #checks if file path is a directory (folder).
ugit.wificonnect(ssid=ssid,password=password) #connects to wifi
```

# Things to note for developers:
Github requires a urequests header otherwise it will give you a 403 error.

Github uses main instead of master for URL api conncetion to repository tree. See source code in ugit.py for more informaiton.

  NOTE if you are pulling from a non-python repository you made need to change call_trees_url to /master? instead of /main? 
  
  giturl = 'https://github.com/{user}/{repository}'
  
  call_trees_url = f'https://api.github.com/repos/{user}/{repository}/git/trees/main?recursive=1'
 
  raw = f'https://raw.githubusercontent.com/{user}/{repository}/master/'

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<img src="images/ugit-logo.png" alt="Logo" width="250" height="100">
<img src="images/ugit_ugit-divider.png" alt="Logo"  height="20">

## Roadmap

See the [open issues](https://github.com/turfptax/ugit/issues) for a list of proposed features (and known issues).

As we test and update the code to work in a variety of scenarious we wish to have the following features implemented as soon as possible.

- Rollback function
- SHA1 internal hash storage - Currently ugit pulls all files
- ugit.py update function - updates the ugit.py code from this repository (currently in dev branch)
- Simplified Logging



