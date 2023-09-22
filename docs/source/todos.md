# Todos
## XYZ
* plugin signals functioning to server before server allows calls
* func return value integration
* get rid of click (no return values possible, really restricted)
* stop pyro messages from appearing
* put loc/line of problem below stack message
* autoreload plugins
* fix wrong plugin calls hiding in nirvana
* no really the whole click thing is just a mess

## Next or running
* Separate plugin package for installation in the venvs
* create a working main branch version
## For big revamp
* API calls inside the same plugin currently still go to the main server. Very inefficient.
* retrieving user vars fails for remote plugins
* Add return values for plugin functions for JS client
* Remote plugins calling other (remote) plugins go the route through the main server. Thats unnecessary
and adds overhead. Especially since each plugin has all the code needed to communicate with other plugins
* Plugins need a close method for freeing resources or similar. Currently even remote plugins just "die"
* Make remote plugins viable (via sending configs over network)
* repair create_wd from terminal
* create build_db for terminal
* standardconfigs for plugins
* change readme to only pull from main branch
* rmeove db from git
* include openai in standard config
* smaller minimum working version
* interactive installaiton i.e. warning of missing venv adding pyenv etc.
## Important
* logging configs are not applied when starting plugins or using code independently
* a prefix venv setting

* global plugin pre settings
* Pyro does not define an async interface. However adding one with some reading up in the [PSL](https://docs.python.org/3/library/asyncio-protocol.html)
should not be that hard. But there are also arguments for simply leaving the threadpoolexecutor. 
* Remote plugin logging to file is currently disabled as safe file access currently isn't implemented
* traceback information for LOG.log_exception potentially wrong. Needs closer look
## General
* if new settings for plugins are added use them as a fallback when not yet specified
* Add basic plugin for nothing but sending commands to running server
* Plugin meta settings currently can't be set via the conf file of the plugin. For most settings this makes sense.
However for the venv_path, allowed_as_standalone, api_only etc it doesn't.
* reload plugins from chat
## Architecture
+ plugin_manager.py and more specificall the _PluginManager are a wild mix of module, instance and singleton pattern.
    
    However since commit `decc6b00` and the restructuring of thread and process local variables that is no
    longer necessary or even smart. It currently prohibits any sort of extension of the plugin system.
