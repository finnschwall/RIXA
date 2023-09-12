# NEVER IMPORT THIS!!!
# This module prepares a process for loading plugins and will therefore alter all sorts of things.
import os
import sys
import pickle
import logging
import logging.config as log_conf
import importlib.machinery
from threading import Thread
import time
from multiprocessing import shared_memory  # , resource_tracker
import importlib
import warnings

warnings.filterwarnings("ignore")

shm_name = sys.argv[1]
shm = shared_memory.SharedMemory(name=shm_name, create=False)
buffer = shm.buf
data = pickle.loads(bytes(buffer[1:]))
shm.buf[0] = 1
to_load = dict(data)

try:
    import Pyro5
    import Pyro5.api
except Exception as e:
    shm.buf[0] = 10
    shm.close()
    raise e

if not to_load["DISABLE_PLUGIN_MODULE_CHECK"]:
    for i in to_load["missing_imports"]:
        try:
            shm.buf[0] = 50
            importlib.import_module(i)
        except:
            print(
                f"INFO: The loading of '{to_load['name']}' has been stopped. The server assumes that the specified venv (exec path: '{to_load['venv_path']}')"
                f" does not fulfill the requirements to load '{to_load['name']}'.\nThe suspected missing module is '{i}'."
                f"\nAdditionally the server estimates these unfulfilled requirements for the plugin: {to_load['missing_imports']}")
            shm.buf[0] = 10
            shm.close()
            exit()

shm.buf[0] = 100
shm.close()
server_settings = to_load["server_settings"]
sys.path.insert(0, to_load["path_to_file"])
sys.path.insert(0, to_load["server_path"])
os.chdir(to_load["path_to_file"])

import plugins.log_helper

logging.setLoggerClass(plugins.log_helper.RIXALogger)
import plugins.conf as plug_conf
import plugins.api as plug_api

to_load["log_conf"]["filters"]["RIXAFilter"]["uid_mode"] = "remote"

# prevent disaster
# to_load["log_conf"]["loggers"]["root"]["handlers"] = ["console"]
# to_load["log_conf"]["loggers"]["root"]["handlers"] = ["console"]
if "file" in to_load["log_conf"]["loggers"]["root"]["handlers"]:
    to_load["log_conf"]["handlers"]["file"]["filename"] = os.path.join(to_load["server_settings"]["WORKING_DIRECTORY"],
                                                                       "log", "plugin_" + to_load["name"] + ".txt")

# from pprint import pp
# pp(to_load["log_conf"], indent=2)
log_conf.dictConfig(to_load["log_conf"])
logger = logging.getLogger()
to_load.pop("log_conf")

plug_conf.p_id = 100
plug_conf.plugin_system_active = True
plug_conf.is_remote = True
plug_conf.is_server = True
plug_conf.cur_conf = to_load
plug_conf.parse_mode = False

loader = importlib.machinery.SourceFileLoader(to_load["name"], to_load["abs_path"])

try:
    plugin_module = loader.load_module()
except Exception as e:
    # logger.error(f"Plugin \"{to_load['name']}\" has failed during import!")
    raise e

Pyro5.config.SERVERTYPE = "multiplex"
plugin_daemon = Pyro5.server.Daemon(port=to_load["port"])


@Pyro5.server.expose
@Pyro5.server.oneway
def shutdown_server():
    global plugin_daemon
    plugin_daemon.shutdown()


plug_conf.call_architecture = to_load["call_architecture"]

if to_load["call_architecture"] == "functional" or to_load["call_architecture"] == "standard":
    dummy = plug_api._create_class("PLUGIN_" + to_load["name"],
                                   list(plug_api._parsed_methods["functions"].values()) + [shutdown_server])
    plugin_controller = plug_api._create_class("PluginController", [shutdown_server])
elif to_load["call_architecture"] == "manual":
    raise NotImplementedError()
else:
    raise Exception(f"Invalid call architecture for '{to_load['name']}'")

try:
    plugin_module.__dict__[to_load["init_name"]]()
except Exception as e:
    logger.log_exception()
    # logger.debug(log_helper.format_exception(e), extra={"is_exception": True})
    if not server_settings["SHOW_ALL_PLUGIN_EXCEPTIONS"]:
        raise e
    # logger.error(
    #     f'Main function of plugin "{to_load["name"]}" has failed to execute! Plugin will be unloaded.\n'
    #     f'Reloading plugin without restarting the server could fail.')

Pyro5.server.serve(
    {
        dummy(): to_load["name"],
        plugin_controller(): "PluginController"
    }, daemon=plugin_daemon, verbose=False, use_ns=False)
print(f"Plugin '{to_load['name']}' finished correctly")
