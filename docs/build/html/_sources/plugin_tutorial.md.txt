# Plugin programming quickstart
## Introduction
The plugin system is based on functional programming i.e. it is basically just a complex composition of functions.
Classes etc. are not really existent here and everything that _looks_ like a class is most of the time not one.

The reason is simple. The server can have many users and each one of them could make a request at the same time. To keep
order each request is translated into a function call. This call contains all necessary API and variables.
But inside this functions namespace other users or their requests are non-existent. 

The plugin system basically is just a way for you to expose functions to the server that it can call.

## Setup
Let's assume you have some code you want to make available to the server. First add the directory with your code
(don't forget the backup) to the conf.py in the plugins app of the RIXA server.

Inside the virtualenvironment of your new plugin you will need to install **Pyro5**.

<details><summary>I don't have a venv</summary><blockquote>
  If you use no packages at all then you don't need one. In any other case now is the time to create one.
I strongly advise against running without a venv even if all the packages are on your system path. 
</blockquote></details>

### Using jupyterlab for development
If you don't want to use jupyterlab or any other ipykernel based system and just want to develop using the webserver
then you can ignore this.

Otherwise be warned that using the plugin system in jupyter is not really supported. If you encounter errors here you
are on your own.

First you will have to install and register an ipykernel for your venv (if you haven't done so already)

``` bash
python3 -m pip install ipykernel
python3 -m ipykernel install --user --name NAME
```

To execute and work with the code you have to use the Pluginloader from the server.

``` python
import RIXAWebserver.plugins
from RIXAWebserver.plugins.plugin_manager import _PluginLoader
plugin_loader = _PluginLoader(jupyter=True)
plugin_loader.parse_plugin(FILENAME, PATH_TO_FILE)
plugin_loader.load_discovered_plugins()
```

You can now execute commands like in the chat using 
``` python
plugin_loader.execute_command(CMD)
```
The API works the same as on the server. All display functions will display below the cell where you initialized the loader.
However (logically) there is no persistent user storage.

To reload the plugins you're using you can either restart the kernel or do this
``` python
plugin_loader._reset():
plugin_loader.parse_plugin(FILENAME, PATH_TO_FILE)
plugin_loader.load_discovered_plugins()
```
Should you encounter problems restart the kernel. The reset function isn't meant for continuous use. 

<style>
  .admonition {
    border: 1px solid #f7c6c7;
    border-radius: 3px;
    padding: 10px;
    margin-bottom: 15px;
  }

  .admonition-title {
    font-weight: bold;
    margin: 0;
    padding-bottom: 5px;
  }

  .admonition-warning {
    background-color: #f8e9e9;
    border-color: #f8bbb1;
    color: #c75c4c;
  }
</style>

<div class="admonition admonition-warning">
  <p class="admonition-title">Warning</p>
  <p>The _PluginLoader class looks like a class but it isn't one! Creating or deleting additional
instances will cause massive problems. A PC restart may be required if done.</p>
</div>

## Developing the plugin
First some warnings.
* Do not generate plugin attributes or variables dynamically 
* All plugin code is parsed and compiled by the RIXA plugin manager.

Let's begin. Suppose you want to develop a simple datafile interface. All real code is already existent you simply want
to make the connection to the server.

Each plugin needs to have an entry point, a main init. There can't be more than one initializer per file.
It could look like this


``` python
standard_config = {"data_path": "raw_data/train.xls", "explanation_path": "raw_data/explanations.txt"}
@plugin_init(namespace="CoolData", venv="/usr/data_venv", config=standard_config, config_is_server_managed=True)
def cool_data(ctx, config, meta_config):
    do_data_stuff()
``` 

We have now defined and created a new plugin. The specifics of the parameters are in the API doc. If we were to enter
> ##--help

in the chat or in our jupyterlab plugin_loader.execute_command we would see a new entry called 'cool_data'.
Now let's add some functionality. Suppose we want to be able to show the user datapoints. That would be as simple as
``` python
@cool_data.plugin_method()
@argument('index', type=api.arg_type.INT)
def get_data_point(api, index):
    row = get_row_somehow(cool_data.ctx.data, index)
    api.display_html(row.to_html())
```
Now a user can simply enter
>##cool_data get-data-point 20

and would see the 20th datapoint as a nicely formatted table.

But the real beauty is: The NLU model can do so too.

For anything more sophisticated look at the rest of the docs.