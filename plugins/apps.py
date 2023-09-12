from django.apps import AppConfig
import importlib
from .plugin_manager import _PluginLoader
from plugins.admin import PluginAdmin
from django.conf import settings
import sys
import logging
from django.utils import autoreload
from django.contrib import admin
logger = logging.getLogger("ServerInitializer")
import os

def restart_hook(**kwargs):
    path = str(kwargs["file_path"])
    if path[-3:] == ".py":
        _PluginLoader.shutdown_server()


class PluginsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'

    name = 'plugins'

    def ready(self):
        if len(sys.argv) > 1 and ("runserver" in sys.argv or 'RIXAWebserver.asgi:application' in sys.argv):
            if os.environ.get('RUN_MAIN') != 'true':
                logger.debug("Autoreloader started")
            else:
                autoreload.file_changed.connect(restart_hook)
                logger.debug("Loading plugins")
                plugin_loader = _PluginLoader()
                plugin_loader.discover_plugins()
                plugin_loader.load_discovered_plugins()
                plugin_loader.finish_loading()
                logger.debug("Finished loading plugins")
                admin.site.__class__ = PluginAdmin

# class Meter():
#     def __init__(self, dev):
#         self.dev = dev
#     def __enter__(self):
#         self.fd = open(self.dev, MODE)
#         return self
#     def __exit__(self, type, value, traceback):
#         close(self.fd)
#
# def __enter__(self):
#     return self
# meter = Meter('dev/tty0')
# with meter as m:
#     import contextlib
#
#
# @contextlib.contextmanager
# def themeter(name):
#     theobj = Meter(name)
#     try:
#         yield theobj
#     finally:
#         theobj.close()  # or whatever you need to do at exit
#
#
# # usage
# with themeter('/dev/ttyS2') as m:
#     # do what you need with m
#     m.read()
#
# import sys
# import subprocess
# def install(pkg,path):
#     return subprocess.check_call([sys.executable, "-m", "pip", "install", pkg,"--target={}".format(path)])
# pkgs = [
# 'scikit-learn==0.24.2',
# 'scikit-learn==0.24.1',
# ]base = 'somepath/'
# for i in pkgs:
#     [name,ver] = i.split('==')
#     path = base+name+'/'+ver
#     print(path)
#     install(i, path)
#
# import os
# import sys
# sys.path.insert(1,os.path.abspath('somepath/scikit-learn/0.24.2'))
# import sklearn
# print(sklearn.__version__)
# #this will be 0.24.2
# ‘1’ inside sys.path.insert increases the priority of the path
