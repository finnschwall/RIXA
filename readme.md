<font size="5">Welcome to <b>RIXA</b><br>
"<b>R</b>eal t<b>I</b>me e<b>X</b>plainable <b>A</b>rtificial Intelligence"
A project for end user focused XAI (and other stuff)</font>

# Description
RIXA is primarily a combination of dashboard and NLP for integration between XAI and a "natural" interface.
The last paper is [this](https://ieeexplore.ieee.org/document/10411695).
Two more are currently pending.

~~This readme aims to give a quick overview for getting started. All technical questions and advanced infos are in the
[docs](https://finnschwall.github.io/RIXA/) .~~

Currently there is no up-to-date readme or docs. The docs here are based on an entirely different (and obsolete) architecture approach.
The most up to date info can be found in the subprojects that now make up most of RIXAs non-web-related-architecture:

[rixaplugin](https://github.com/finnschwall/rixaplugin) for integrating (XAI) Code for usage in a dashboard or by an LLM

[pyalm](https://github.com/finnschwall/PyALM) as backend for various (local) LLMs

[rixarag](https://github.com/finnschwall/rixarag) for RAG (retrieval augmented generation) and vector databases


# Screenshots

## RIXA based decision support system
![Screenshot](screenshots/xai_chat_histo_cfs.png)
## RIXA chat with RAG and plot
![Screenshot](screenshots/rag_and_plot.png)
## RIXA based dashboard
![Screenshot](screenshots/dashboard.png)

See more in the [screenshots folder](https://github.com/finnschwall/RIXA/tree/main/screenshots).

# EVERYTHING BELOW IS NO LONGER UP TO DATE

<br><br><br>
# Quickstart
## Demo
There is no _public_ demo currently :(
## Documentation
[Here](https://finnschwall.github.io/RIXA/) for the latest main branch version.
For all other versions (also locally) it is under docs/build/html. For branches other
than main you will have to build it.
## Installation
**Hardware requirements**

Basically none for the pure server (<300 MB of RAM, negligible CPU time). The requirements come from the plugins
and the chat backend. If you want to use local LLMs I would
recommend at least 12 GB RAM, 8 GB VRAM and a decent CPU with AVX2 support.

**UNFINISHED**

### For developers
For the server you need Python>=3.10.

Server + Plugin API:
```bash
pip3 install rixa
```
Plugin API only. Works with lower python versions but functionality may be reduced.
```bash
pip3 install git+https://github.com/finnschwall/RIXA#subdirectory=plugins
```
RIXA works fine without venvs, conda, pyenv etc. But it comes with extensive support for all of those.
The "RIXA way" is to install plugins with different requirements in different environments so plugin dependencies
don't interfere with each other.

## Starting and running the server

## Creating the working directory (wd)

### For endusers
Just start RIXA via terminal
```bash
rixaserver runserver
```
or desktop shortcut.

The instructions below can also be used in the enduser installation, however defaults are supplied.
Also a working directory is automatically created and managed in the RIXA data folder.
### For developers
#### Setup
The server requires a directory to work from that contains temporary files, databases, config files etc.
Such a directory can be created either by supplying path or by navigating to a folder.
```bash
#A
rixaserver initialize-dir PATH
#B
rixapserver initialize-dir
```

A local database is automatically created when you create a new WD. Should you switch the RIXA version and encounter errors you can
update the db scheme with

```bash
rixaserver update_db 
```
Should you otherwise encounter errors and there is nothing of interest in the db you can rebuild it at any time with
```bash
rixaserver update_db --rebuild
```
That is also necessary should you e.g. switch to mysql.

If conservation of the dbs contents is important you will have to use djangos managment commands to manually
alter the db. All of djangos managment commands are available through

```bash
rixaserver django
```

#### Running the server
To run the server you must be in the wd. Alternatively you can set the wd as an env var like this:
```bash
export RIXA_WD=PATH
```


Then you can run
```bash
rixaserver runserver
#or alternatively specify port and ip. This will open the server to your entire network.
rixaserver runserver localhost:8000
```
The `runserver` command is a link to djangos `runserver` with some settings of paths before running.




# Developing and adding plugins
In the wd there is a plugin folder. This folder is always added to the search paths for plugins.
Other search paths and more complex configurations have to be done using the `config.ini`.
There are some helpful commands for all of this available in
```bash
rixaserver
```


# FAQ
## I encounter a shared_memory warning when the server closes
```bash
UserWarning: resource_tracker: There appear to be 1 leaked shared_memory objects to clean up at shutdown
```
If it looks something like this then you can ignore it. [See issues pages](docs/build/html/issues.html).

## I would like to use a version managment system
I recommend [pyenv](https://github.com/pyenv/pyenv) with [venv plugin](https://github.com/pyenv/pyenv-virtualenv).
In the docs under the [advanced installation](MISSING) page the most important steps are listed to get both running
with RIXA.


## Branches?

You can install from three branches. There is `main`, `beta` and `dev`.

`main` aims to provide stable code.
`beta` is semistable and should reflect newer features _currently nonexistent_. `dev` is for ongoing development.
Unless you have a very good reason don't touch the `dev` branch. It seldom contains a working version.

If you install it will automatically be built from `main`. For `dev` or `beta` you can use for the server:
```bash
pip3 install git+https://gitlab.cc-asp.fraunhofer.de/xai-hiwi/rixa/rixawebserver.git@dev
```
and for the plugins
```bash
pip3 install git+https://gitlab.cc-asp.fraunhofer.de/xai-hiwi/rixa/rixawebserver.git@dev#subdirectory=plugins
```
For options add a hashtag at the end with the build option following. Several options can be delimited by an
ampersand.


If you wish to have a look at the dev branch then a local installation is recommended. 
Pull the repo and[^1]

```bash
pip install -e PATH_TO_PROJECT
```
Options are supported here too.
```bash
pip install -e PATH_TO_PROJECT[OPTION]
```
[^1]: Pulling and not installing is not supported. It will likely lead to path issues.
### Package options

There are currently two options for the installation: `standard` and `doc`. It is strongly recommended to install
with `standard`. Otherwise the standard plugins will not work.
If you want to be able to build the docs you also need `doc`. For installing e.g. with full:


# Everything else
[See docs for everything else](https://finnschwall.github.io/RIXA/))


