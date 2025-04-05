# Installation

<h1><img src="https://cdn-icons-png.flaticon.com/512/3261/3261386.png"  width="100" height="100">Broken page!</h1>


## Python Version
The primary python version for the server is `3.1.1`. But it *should* run on all python versions > 3. More on that in [pyenv](#pyenv-target)

## Preparing the environment

### Quick way
Likely there is venv on your system. So you can simply install the requirements and then run the server.
That looks something like this

```bash
echo "Installing requirements for building python"
sudo apt update; sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

echo "Installing pyenv"
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
cd ~/.pyenv && src/configure && make -C src

echo "Installing venv support plugin for pyenv"
git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv

echo "Setting up bash integration"
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

#load new vars into bash
source ~/.bashrc

echo "Installing and setting up RIXA server"
pyenv install 3.11
pyenv shell 3.11
pyenv virtualenv rixa_webserver
pyenv virtualenv rixa_plugins

pyenv activate rixa_webserver
git clone https://gitlab.cc-asp.fraunhofer.de/xai-hiwi/rixa/rixawebserver.git
pip3 install -e .[dev]

pyenv deactivate

pyenv activate rixa_plugins
echo "Installing requirements for standard plugins"
pip3 install pyro5 sympy sentence_transformers pandas plotly
echo "Use this path + '/bins/python3' for the 'venv_path' attribute for all the standard plugins."
echo pyenv prefix rixa_plugins
pyenv deactivate

```
