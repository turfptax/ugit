<br />
<div align="center">
    <img src="images/logo.png" alt="Logo" width="150" height="150">
    <h1 align="center">Micropython OTA Updates</h1>
  <h3 align="center">Keep your remote ESP32 devices in sync with a github repo.</h3>
  <p align="center"> Over The Air, with one command: ugit.pull_all()</p>
</div>


## About ugit

THis is meant to clone an entire micropython repository to an internet enable micropython microcontroller

ugit functions:
* ugit will update the internal file structure of an ESP32 with a github repository
* Files Folders and file Deletions are updated to the board
* Specify which repository, ingore files, and user inside of ugit_config.py

With ugit you can update a micropython board with a complete micropython library from github.

Download `ugit.py` to your ESP32 micropython board to get started.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

boot.py

import ugit

ugit.pull_all()


### Installation

_Below is an example of how you can instruct your audience on installing and setting up your app. This template doesn't rely on any external dependencies or services._

1. Copy ugit.py onto your micropython board
2. modify ugit_config with the user,repository,ssid, and password
4. run the ugit.pull_all()


<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

code:

import ugit

ugit.pull_all()

### TESTING:

import ugit

ugit.build_internal_tree() grabs internal file structure
ugit.pull(local_file_path,raw_file_url) pulls single raw files
ugit.pull_git_tree() pulls the github file tree from the repository
ugit.parse_git_tree() parses the github tree file to stdout
ugit.is_directory() checks if file path is a directory (folder).
ugit.wificonnect(ssid=ssid,password=password)

# Things to note for developers:
Github requires a urequests header otherwise it will give you a 403 error.

Github uses main instead of master for URL api conncetion to repository tree. See source code in ugit.py for more informaiton.

  NOTE if you are pulling from a non-python repository you made need to change call_trees_url to /master? instead of /main? 
  
  giturl = 'https://github.com/{user}/{repository}'
  
  call_trees_url = f'https://api.github.com/repos/{user}/{repository}/git/trees/main?recursive=1'
 
  raw = f'https://raw.githubusercontent.com/{user}/{repository}/master/'

## Repository urepl is used to connect to the internet, it is another library i'm working on for UDP ascyncronus REPL. Check it out on github to learn more.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
