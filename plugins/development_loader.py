import sys
import os
import asyncio
from asgiref.sync import async_to_sync

parent_dir = os.path.dirname(os.path.dirname(__file__))
settings_path = os.path.join(parent_dir, "RIXAWebserver")
plugin_path = os.path.join(parent_dir, "plugins")
sys.path.insert(0, parent_dir)
sys.path.insert(0, settings_path)
sys.path.insert(0, plugin_path)

_loader = None
_logger = None

def initialize_plugin_system(jupyter=True, wd_path=None):
    global _loader, _logger
    if _loader:
        raise Exception("Plugin system has already been loaded in this process!")
    if wd_path:
        os.environ["RIXA_WD"] = os.path.abspath(wd_path)

    os.environ["DJANGO_SETTINGS_MODULE"] = "RIXAWebserver.settings"

    from plugins.plugin_manager import _PluginLoader, settings
    import logging as _logging

    globals()["_PluginLoader"] = _PluginLoader
    globals()["settings"] = settings
    globals()["_logging"] = _logging

    from django.conf import settings
    import logging.config as _log_conf
    _log_conf.dictConfig(settings.LOGGING)
    _logger = _logging.getLogger()
    _PluginLoader.catch_exceptions = False
    _loader = _PluginLoader(jupyter=jupyter)

def create_fake_api():
    global _loader
    import api
    return api.JupyterAPI(_loader.handle1, _loader.handle2)

def get_server_logger():
    return _logger

def unload_all_plugins():
    global _loader
    _logger.warning("This method can lead to unforeseen behaviour. If you encounter problems reload python.")
    _PluginLoader._reset()


def unload_plugin():
    global _loader
    _logger.warning("This method can lead to unforeseen behaviour. If you encounter problems reload python.")


def discover_plugins(paths=None):
    global _loader
    return _loader.discover_plugins(paths)


async def execute_command(cmd):
    global _loader
    await _PluginLoader.execute_command(cmd, "JUPYTER")
    print("Finished")


def reload_plugin(name):
    _loader.reload_plugin(name)

def get_plugin_search_paths():
    return settings.PLUGIN_PATHS


def parse_plugin(file_path):
    global _loader
    filename = os.path.basename(file_path)
    path = os.path.dirname(file_path)
    conf = _loader.parse_plugin(path, filename)
    return conf


def load_plugin(name):
    exit_code = _loader.load_plugin(name)


def load_discovered_plugins():
    _loader.load_discovered_plugins()
