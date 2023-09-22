# Unless you really know what you are doing importing this module or any of it's contents is a bad idea.
# Under no circumstances import any of this outside the main thread/process
import asyncio
import gc
import inspect
import re
import threading
from io import StringIO
from threading import Thread
import os.path
import sys
from abc import ABC
import pickle
import Pyro5.server
import Pyro5
import click as _click
from copy import copy as _copy
import os as _os
import sys as _sys
import ast as _ast
import platform
import pkgutil as _pkgutil
import types as _types
import importlib as _importlib
import warnings as _warnings
from os.path import isfile, join
import gc as _gc
from django.conf import settings
import subprocess
from asgiref.sync import async_to_sync
import importlib.machinery
import concurrent.futures
import signal
import weakref
from collections import defaultdict
from plugins import api
import psutil
import plugins.conf as plugin_conf
import logging
import atexit
from multiprocessing import shared_memory
import time
import socket
import json
from importlib import abc
import click.core

_logger = logging.getLogger("PluginManager")


def captured_echo(message, file=None, nl=True, err=False, color=None):
    _PluginLoader.captured_message = message


setattr(click.core, "echo", captured_echo)

public_variables = {}


class _Namespace:
    def __init__(self, av_commands):
        self.__dict__.update(av_commands)

    def __setattr__(self, name, value):
        raise NameError("Adding new functions or values to this context is disallowed.")

    def __str__(self):
        return self._name

    def __repr__(self):
        return self._name


@_click.group(name="RIXA", add_help_option=False)
@_click.pass_context
async def _cmd_group_hook(ctx):
    pass


def build_plugin_function_dict(plugin_entry, plugin_name):
    ctx = click.Context(plugin_entry)
    func_list = []
    iter_dic = ctx.to_info_dict()["command"]["commands"]
    for i in iter_dic:
        if i == "help":
            continue
        par_prop = {}
        required = []
        for par in iter_dic[i]["params"]:  # _name, par_info in iter_dic[i]["params"].items():
            if par["name"] == "help":
                continue
            conv_dic = {"Bool": "boolean", "Float": "number", "Int": "integer", "String": "string"}
            par["type"]["param_type"] = conv_dic[par["type"]["param_type"]]
            par_prop[par["name"]] = {"type": par["type"]["param_type"]}
            if "help" in par:
                par_prop[par["name"]]["description"] = par["help"]
            if par["required"]:
                required.append(par["name"])
        params = {"type": "object", "properties": par_prop}
        fun_exp = {"name": f"{plugin_name}__{i}", "parameters": params, "required": required}
        if iter_dic[i]["help"]:
            fun_exp["description"] = iter_dic[i]["help"]
        func_list.append(fun_exp)
    return func_list


def json_hook(obj):
    return str(type(obj))


class _PluginLoader:
    loaded_plugins = {}
    found_plugins = {}
    singleton = None
    has_shut_down = False
    captured_message = ""

    main_plugin_entry = _click.Group(name="RIXA", no_args_is_help=False)

    def __init__(self, as_server=True):
        if as_server:
            atexit.register(_PluginLoader.shutdown_server)
            #
            signal.signal(signal.SIGINT, _PluginLoader.shutdown_server)
            self.none_api = api.NoneAPI("NONE")
            self.consumer_api = defaultdict(lambda: self.none_api)
            ports = {}
            for i in psutil.net_connections():
                pid = i.pid
                if pid:
                    process = psutil.Process(pid)
                    process_name = process.name()
                else:
                    process_name = "unknown"
                port = i.laddr.port
                ports[port] = process_name

            port_list = list(ports.keys())
            port_list.sort()
            diffs = [port_list[i + 1] - port_list[i] for i in range(len(port_list) - 1)]
            sort_diff = max(range(len(diffs)), key=lambda i: diffs[i])
            start_port = port_list[sort_diff] + 1
            self.pyro_port = start_port
            self.current_port = start_port + 1
            self.pyro_daemon = Pyro5.server.Daemon(port=start_port)
            self.pyro_server_thread = Thread(target=Pyro5.server.serve, args=({},),
                                             kwargs={"daemon": self.pyro_daemon, "use_ns": False, "verbose": False})
            self.pyro_server_thread.start()
            # if jupyter:
            #     from IPython.display import display as jup_display
            #     self.handle1, self.handle2 = jup_display("Plots", display_id=True), jup_display("Chat", display_id=True)
            #     self.consumer_api["JUPYTER"] = api.JupyterAPI("JUPYTER", self.handle1, self.handle2)
            #
            #     jupyter_sync_api = api.JupyterSyncAPI("JUPYTER", self.handle1, self.handle2)
            #     self.pyro_daemon.register(jupyter_sync_api, "JUPYTER")


        python_version = platform.python_version_tuple()[1]
        if int(python_version) <10:
            self.standard_modules = set()
            settings.DISABLE_PLUGIN_MODULE_CHECK = True
            _logger.warning("The interpreters python version is >3.10. Server will run in maixmum compatability mode."
                            "Features like package managment, advanced import system etc. are disabled.")
        else:
            self.standard_modules = _sys.stdlib_module_names
        self.main_thread_packages = set([x.name for x in list(_pkgutil.iter_modules()) if x.ispkg == True])
        self.main_thread_packages.update(set(["plugins", "api", "rixawebserver"]))
        # self.main_thread_packages.add("plugin_manager")

        plugin_conf.plugin_system_active = True
        self.plugin_number = 0

        self.loaded_functions = api._parsed_methods
        _PluginLoader.singleton = self

        public_variables["active_user_connections"] = ThreadSafeCounter()

        executor = CountingThreadPoolExecutor(max_workers=settings.MAX_BLOCKING_CALLS,
                                              thread_name_prefix="EXECUTOR_")
        public_variables["task_threadpool"] = executor
        public_variables["loaded_plugins"] = _PluginLoader.loaded_plugins
        public_variables["found_plugins"] = _PluginLoader.found_plugins

    @staticmethod
    def register_consumer(channel_name, scope):
        if not plugin_conf.async_loop:
            plugin_conf.async_loop = asyncio.get_running_loop()
            plugin_conf.async_loop.set_default_executor(public_variables["task_threadpool"])

        pl_loader = _PluginLoader.singleton
        new_api = api._LocalAPI(channel_name, scope)

        def sync_func_factory(name, async_api):

            @Pyro5.server.expose
            def wrapped(*args, **kwargs):
                async_to_sync(getattr(async_api, name))(*args, **kwargs)

            wrapped.__name__ = name
            return wrapped

        funcs = []
        for i in dir(new_api):
            if i[0] == "_":
                continue
            prop = getattr(new_api, i)
            if inspect.ismethod(prop) or inspect.isfunction(prop):
                funcs.append(sync_func_factory(i, new_api))
        new_sync_api = api._create_class("SyncAPI", funcs)
        pl_loader.consumer_api[channel_name] = new_api
        pl_loader.pyro_daemon.register(new_sync_api, channel_name)
        return new_api

    @staticmethod
    def unregister_consumer(channel_name):
        pl_loader = _PluginLoader.singleton
        if channel_name not in pl_loader.consumer_api:
            _logger.warning("Attempt to unregister non-existing consumer API.")
        else:
            del pl_loader.consumer_api[channel_name]

    @staticmethod
    async def call_nlp_model(msg, uid):
        # pp(_PluginLoader.loaded_plugins[settings.NLP_BACKEND]["callables"])
        api_obj = _PluginLoader.singleton.consumer_api[uid]
        await _PluginLoader.loaded_plugins[settings.NLP_BACKEND]["callables"]["get_answer"](api_obj, msg)

    @staticmethod
    async def execute_command(cmd, uid):
        api_obj = _PluginLoader.singleton.consumer_api[uid]
        try:
            args = re.findall(r'(?:"[^"]*"|[^\s"])+', cmd)  # [x for x in cmd.split(" ") if x != ""]
            _PluginLoader.captured_message = ""
            future = _PluginLoader.main_plugin_entry(args, standalone_mode=False, prog_name="main", obj=api_obj)
            if type(future).__name__ == "coroutine":
                ret_val = await future
            if type(future) == dict and "exc_type" in future:
                await api_obj.display_in_chat(f"Error while parsing command: {future['exc_message']}")
            if _PluginLoader.captured_message != "":
                await api_obj.display_in_chat({"role": "server", "content": _PluginLoader.captured_message})

        except Exception as e:
            if type(e).__name__ in ["UsageError", "MissingParameter", "NoSuchOption"]:
                # "A command has been detected that likely has syntax errors."
                await api_obj.display_in_chat(f"Error while parsing command: {str(e.args[0])}")
            elif settings.SHOW_ALL_PLUGIN_EXCEPTIONS:
                _logger.log_exception()

    @staticmethod
    def _reset():
        del _PluginLoader.found_plugins
        del _PluginLoader.loaded_plugins
        _gc.collect()
        _PluginLoader.found_plugins = {}
        _PluginLoader.loaded_plugins = {}

    def finish_loading(self):
        full_info = []
        for val in _PluginLoader.loaded_plugins.values():
            if len(val) == 0:
                continue
            full_info += val["callable_info"]
        plugin_conf.all_available_functions = full_info

        if settings.NLP_BACKEND != "none":
            if settings.NLP_BACKEND not in plugin_conf.available_nlp_backends:
                settings.NLP_BACKEND = "none"
                _logger.warning("Specified NLP backend not found!")
        for i in api._parsed_methods:
            for j in api._parsed_methods[i]["original"]:
                api._available_functions[f"{i.lower()}__{j.lower()}"] = api._parsed_methods[i]["original"][j]
        _logger.info(f"Loaded plugins: \"{list(_PluginLoader.loaded_plugins.keys())}\"")
        _logger.debug(f"All registered functions: \"{list(api._available_functions.keys())}\"\n"
                      f"Remote plugins: {[x for x in _PluginLoader.loaded_plugins if _PluginLoader.loaded_plugins[x]['is_remote']]}")

    def clean(self):
        _warnings.warn("Don't use!", DeprecationWarning)
        _logger.warning("Reloading plugins is now no longer possible through 'load_plugin'")
        del _PluginLoader.found_plugins

    def load_discovered_plugins(self):
        for i in _PluginLoader.found_plugins:
            if i not in settings.EXCLUDED_PLUGINS:
                self.load_plugin(i)

    def load_plugin(self, name, reload=True):
        if name not in _PluginLoader.found_plugins:
            raise Exception(
                f"{name} is not an existing plugin. Available plugins are: {list(_PluginLoader.found_plugins.keys())}")
        if reload and name in _PluginLoader.loaded_plugins:
            self.reload_plugin(name)
            return

        if _PluginLoader.found_plugins[name]["is_local"]:
            self.load_plugin_as_local(name)
        else:
            self.load_plugin_as_remote(name)

    def reload_plugin(self, name):
        if name not in _PluginLoader.loaded_plugins:
            raise Exception(f"{name} has not been found in the currently loaded plugins.")
        path = _PluginLoader.found_plugins[name]["path_to_file"]
        filename = _PluginLoader.found_plugins[name]["filename"]
        del _PluginLoader.loaded_plugins[name]
        del _PluginLoader.found_plugins[name]
        _gc.collect()
        conf = self.parse_plugin(path, filename)
        new_name = conf["name"]
        if new_name != name:
            _logger.warning("Plugin name changed while reloading.")
        self.load_plugin(new_name)

    def load_plugin_as_remote(self, name):

        to_load = _PluginLoader.found_plugins[name]

        result = 1
        for i in range(10):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind('127.0.0.1', self.current_port)
                sock.close()
                result = 0
                break
            except:
                sock.close()
                self.current_port += 1
        if result != 1:
            _logger.critical("Unable to find free port!")
            return
        to_load["port"] = self.current_port
        self.current_port += 1

        if to_load["venv_path"] is None:
            to_load["venv_path"] = sys.executable

        # "pyenv prefix VENV" for path to VENV
        python_venv_path = to_load["venv_path"]

        script_path = os.path.join(settings.BASE_DIR, "plugins", "external_loader.py")

        transfer_dic = dict(to_load)
        transfer_dic.pop("plugin_type")
        transfer_dic["remote_port"] = self.pyro_port
        transfer_dic["log_conf"] = settings.LOGGING
        transfer_dic["server_path"] = str(settings.BASE_DIR)

        # transfer_dic["plugin_path"] = settings.BASE_DIR
        transfer_dic["server_settings"] = {"SHOW_ALL_PLUGIN_EXCEPTIONS": settings.SHOW_ALL_PLUGIN_EXCEPTIONS,
                                           "WORKING_DIRECTORY": settings.WORKING_DIRECTORY}
        transfer_dic["DISABLE_PLUGIN_MODULE_CHECK"] = settings.DISABLE_PLUGIN_MODULE_CHECK

        # read, write = os.pipe()
        to_write = pickle.dumps(transfer_dic, protocol=4)
        byte_array = bytearray(to_write)

        shm_a = shared_memory.SharedMemory(create=True, size=len(byte_array) + 1)
        shm_a.buf[1:len(byte_array) + 1] = byte_array
        shm_a.buf[0] = 0
        if settings.IGNORE_PLUGIN_WARNINGS:
            os.environ["PYTHONWARNINGS"] = "ignore"
        try:
            plugin_process = subprocess.Popen(
                [python_venv_path, script_path, shm_a.name],
                # stderr=subprocess.PIPE,
                # stdin=write,
                # stdout=subprocess.PIPE
            )
        except Exception as e:
            _logger.log_exception()
            shm_a.close()
            shm_a.unlink()
            _logger.critical(f"Loading {to_load['name']} has failed!")
            return

        max_iters = settings.MAX_LOAD_TIME_PER_MODULE
        failed = True
        for i in range(10000):
            time.sleep(0.01)
            if shm_a.buf[0] == 10:

                _logger.error(f"Plugin {transfer_dic['name']} couldn't be loaded!")
                return
            if shm_a.buf[0] == 100:
                failed=False
                break
            if shm_a.buf[0] == 50:
                max_iters += settings.MAX_LOAD_TIME_PER_MODULE
            if i == max_iters:
                _logger.critical(f"Plugin \"{transfer_dic['name']}\" has timed out while loading. "
                                 f"There could be memory leaks!")
                break
        try:
            shm_a.close()
            shm_a.unlink()
        except:
            pass

        if failed:
            return

        plugin_conf.is_remote = True
        plugin_conf.is_server = False
        plugin_conf.parse_mode = False
        plugin_conf.plugin_system_active = True
        plugin_conf.cur_conf = to_load

        code_to_load = to_load["local_code"]
        to_execute = compile(code_to_load, to_load["filename"], mode="exec")
        plugin_module = _types.ModuleType(to_load["name"], 'Local clone for API emulation')
        _PluginLoader.parse_mode = False
        _PluginLoader.cur_conf = to_load
        try:
            exec(to_execute, plugin_module.__dict__)
        except Exception as e:
            _logger.log_exception()
            _logger.critical(f"Erroneous code in {to_load['name']}")
            _PluginLoader.parse_mode = True
            return 1

        _PluginLoader.parse_mode = True
        loaded_config = {"full_module": plugin_module, "is_remote": True,
                         "plugin_controller": Pyro5.api.Proxy(f"PYRO:PluginController@localhost:{to_load['port']}"),
                         "port": to_load["port"], "callables": api._parsed_methods[name]["original"],
                         "callable_info": build_plugin_function_dict(
                             plugin_module.__dict__[to_load["init_name"]]._cmd_group, to_load["name"]) if not to_load[
                             "hidden_in_function_dic"] else []}

        if settings.GENERATE_INTERMEDIARY_FILES:
            with open(os.path.join(settings.DEBUG_PATH, f"{name}_config.json"), "w") as f:
                json.dump(loaded_config, f, skipkeys=True, indent=4, default=json_hook)

        _PluginLoader.loaded_plugins[to_load["name"]] = loaded_config
        _PluginLoader.main_plugin_entry.add_command(plugin_module.__dict__[to_load["init_name"]]._cmd_group,
                                                    name=to_load["name"], )

        return plugin_process

    def load_plugin_as_local(self, name):
        to_load = _PluginLoader.found_plugins[name]
        plugin_conf.parse_mode = False
        plugin_conf.plugin_system_active = True
        plugin_conf.cur_conf = to_load
        plugin_conf.is_remote = False
        plugin_conf.is_server = False

        loader = importlib.machinery.SourceFileLoader(to_load["name"], to_load["abs_path"])

        try:
            plugin_module = loader.load_module()
        except Exception as e:
            if settings.SHOW_ALL_PLUGIN_EXCEPTIONS:
                _logger.log_exception()
            plugin_conf.parse_mode = True
            return 1

        plugin_conf.parse_mode = True

        try:
            plugin_module.__dict__[to_load["init_name"]]()
        except Exception as e:
            if settings.SHOW_ALL_PLUGIN_EXCEPTIONS:
                _logger.log_exception()
            _logger.error(
                f'Main function of plugin "{to_load["name"]}" has failed to execute! Plugin will be unloaded.')
            return 1

        loaded_config = {"full_module": plugin_module, "is_remote": False,
                         "callables": api._parsed_methods[name]["original"],
                         "callable_info": build_plugin_function_dict(
                             plugin_module.__dict__[to_load["init_name"]]._cmd_group, to_load["name"]) if not to_load[
                             "hidden_in_function_dic"] else []}

        if settings.GENERATE_INTERMEDIARY_FILES:
            with open(os.path.join(settings.DEBUG_PATH, f"{name}_config.json"), "w") as f:
                json.dump(loaded_config, f, skipkeys=True, indent=4, default=json_hook)

        _PluginLoader.loaded_plugins[to_load["name"]] = loaded_config
        _PluginLoader.main_plugin_entry.add_command(plugin_module.__dict__[to_load["init_name"]]._cmd_group,
                                                    name=to_load["name"])

    def extract_config(self, module_body, cur_module_number):
        global_vars = [x for x in module_body if type(x) == _ast.Assign]

        funcs = [i for i in module_body if type(i) == _ast.FunctionDef]
        for i in funcs:
            if len(i.decorator_list) != 0:
                for j in i.decorator_list:

                    func_id = j.func.id
                    if func_id == "plugin_init":
                        init = _copy(i)
                        init.body = [_ast.Module(body=[_ast.Pass()], type_ignores=[])]
                        orig_name = init.name
                        init.name = f"orig_nameX{init.name}Xcur_mod_numX{cur_module_number}"

                        # TODO compile AST tree directly
                        # compileable = _ast.Module(body=[init], type_ignores=[])
                        # compileable=_ast.fix_missing_locations(compileable)
                        global_vars.append(init)
                        to_execute = compile(_ast.unparse(global_vars), "<modified>", mode="exec")
                        locals()["plugin_init"] = api.plugin_init
                        locals()["PluginType"] = api.PluginType
                        executed = exec(to_execute)
                        init_func = locals()[init.name]
                        conf = init_func.plugin_config
                        conf["init_name"] = orig_name
                        return conf

    def discover_plugins(self, paths=None):
        if paths is None:
            paths = settings.PLUGIN_PATHS
        for i in paths:
            if not _os.path.isdir(i):
                continue
            files = [f for f in _os.listdir(i) if isfile(join(i, f))]
            py_files = [f for f in files if f[-3:] == ".py"]
            for j in py_files:
                self.parse_plugin(i, j)
        if len(_PluginLoader.found_plugins) > 0:
            _logger.debug(f"Found plugins: {list(_PluginLoader.found_plugins.keys())}")
        else:
            _logger.debug("No plugins have been found.")

    def parse_plugin(self, path, filename):
        self.plugin_number += 1
        rel_path = join(path, filename)
        with open(rel_path, "r") as f:
            try:
                parsed = _ast.parse(f.read(), filename=filename)
            except Exception as e:
                if settings.SHOW_ALL_PLUGIN_EXCEPTIONS:
                    _logger.log_exception()
                return
            imports = [x.names[0].name for x in parsed.body if type(x) == _ast.Import]
            imports_from = [x.module for x in parsed.body if (type(x) == _ast.ImportFrom and x.level == 0)]
            absolute_imports = imports + list(set(imports_from) - set(imports))
            relative_imports = [x.module for x in parsed.body if (type(x) == _ast.ImportFrom and x.level > 0)]
            absolute_imports = [i.split(".")[0] for i in absolute_imports]

            missing_imports = list(set(absolute_imports) - (self.main_thread_packages | self.standard_modules))
            missing_imports = [i.split(".")[0] for i in missing_imports]

            glob_vars = {x.targets[0].id: (x.value.value if type(x.value) == _ast.Constant else 0) for x in parsed.body
                         if type(x) == _ast.Assign}

            plugin_config = self.extract_config(parsed.body, self.plugin_number)
            if plugin_config == None:
                _logger.debug(f"{filename}' is in one of the plugin folders but doesn't have a (valid) config.")
                return 1

            if not plugin_config["is_local"]:
                for i, node in enumerate(parsed.body):
                    if type(node) == _ast.Import:
                        imp_name = node.names[0].name.split(".")[0]
                        if imp_name in missing_imports:
                            parsed.body[i] = _ast.Expr(_ast.Constant(_ast.dump(node, annotate_fields=False)))
                    if type(node) == _ast.ImportFrom:
                        imp_name = node.module.split(".")[0]
                        if imp_name in missing_imports:
                            parsed.body[i] = _ast.Expr(_ast.Constant(_ast.dump(node, annotate_fields=False)))
                    if type(node) == _ast.FunctionDef:
                        node.body = [_ast.Pass()]

            plugin_config["local_code"] = _ast.unparse(parsed)

            conf_dic = {"absolute_imports": absolute_imports,
                        "relative_imports": relative_imports, "missing_imports": missing_imports,  # "_ast": parsed,
                        "filename": filename, "rel_path": rel_path,
                        "abs_path": _os.path.abspath(rel_path), "path_to_file": path}
            conf_dic.update(plugin_config)
            name = plugin_config["name"] if plugin_config["name"] else filename[:-3]
            conf_dic["name"] = name

            if name in _PluginLoader.found_plugins:
                if name in _PluginLoader.loaded_plugins:
                    raise Exception(f"{name} is already parsed and loaded")
                _logger.info(f"Overwriting old plugin definition for {name}")

            path_to_config = os.path.join(settings.WORKING_DIRECTORY, "plugin_configurations", f"{name}.json")

            if os.path.exists(path_to_config):
                with open(path_to_config, "r") as f:
                    try:
                        conf_dic["config"] = json.load(f)
                    except Exception as e:
                        _logger.error(f"Faulty configuration file for '{name}'. Plugin will not be loaded."
                                      f"The erroneous file is '{path_to_config}'\n{str(e)}")
                        return
            else:
                with open(path_to_config, "w") as f:
                    json.dump(conf_dic["config"], f, indent=2)

            if settings.GENERATE_INTERMEDIARY_FILES:
                with open(os.path.join(settings.DEBUG_PATH, f"{name}_dummy.pym"), "w") as f:
                    f.write(plugin_config["local_code"])

            if "config" in conf_dic and conf_dic["config"] and "venv_path" in conf_dic["config"] and \
                    conf_dic["config"]["venv_path"]:
                conf_dic["venv_path"] = conf_dic["config"]["venv_path"]

            if not conf_dic["is_local"]:
                # from pprint import pp
                # del conf_dic["local_code"]
                # pp(conf_dic)
                if not conf_dic["venv_path"]:
                    if settings.DEFAULT_PLUGIN_VENV:
                        conf_dic["venv_path"] = settings.DEFAULT_PLUGIN_VENV
                if conf_dic["venv_path"] and len(conf_dic["venv_path"].split(":")) > 1:
                    venv_type, env_name = conf_dic["venv_path"].split(":")
                    if venv_type == "pyenv":
                        result = subprocess.run(["pyenv", 'prefix', env_name], capture_output=True, text=True)
                        if result.returncode == 0:
                            conf_dic["venv_path"] = os.path.join(result.stdout.split("\n")[0],"bin","python3")
                        else:
                            error_message = result.stderr
                            _logger.error(
                                f"Unable to determine venv path for'{conf_dic['name']}': {error_message}")
                            return
                if conf_dic["venv_path"] and not os.path.exists(conf_dic["venv_path"]):
                    _logger.error(
                        f"\"{conf_dic['name']}\" has been specified as an extern plugin but the provided venv path"
                        f" does not exist! This plugin will not be loaded.")
                    return
                if conf_dic["venv_path"]:
                    result = subprocess.run([conf_dic["venv_path"], '-m', 'pip', 'freeze', '--local'],
                                            capture_output=True,
                                            text=True)
                    if result.returncode == 0:
                        av_packages = result.stdout
                    else:
                        error_message = result.stderr
                        _logger.critical(
                            f"While trying to check for missing packages for '{conf_dic['name']}' something went"
                            f"wrong in the venv: {error_message}")
                    av_packages = av_packages.split("\n")
                    av_packages = set([i.split("==")[0].replace("-", "_") for i in av_packages])
                    all_av_packages = av_packages | {"plugins"} | self.standard_modules
                    missing_imports = list(set(absolute_imports) - all_av_packages)
                    if len(missing_imports) > 0 and not settings.DISABLE_PLUGIN_MODULE_CHECK:
                        _logger.error(f"The server thinks the venv ({conf_dic['venv_path']}) which you specified for '{plugin_config['name']}'"
                                         f" does not contain all packages required for running the plugin.\nAssumed "
                                         f"missing are: {missing_imports}'.\nThis plugin will be skipped!")
                        return
            else:
                if len(missing_imports) > 0 and not settings.DISABLE_PLUGIN_MODULE_CHECK:
                    _logger.error(f"The server detected missing package(s) for the local plugin '{plugin_config['name']}'."
                                     f" Assumed missing are: {missing_imports}'.\nThis plugin will be skipped!")
                    return
            _PluginLoader.found_plugins[name] = conf_dic
            return conf_dic

    @staticmethod
    def shutdown_server(signum=None, frame=None, **kwargs):
        if not _PluginLoader.has_shut_down:
            _PluginLoader.has_shut_down = True
            loader = _PluginLoader.singleton
            for key, val in _PluginLoader.loaded_plugins.items():
                if val["is_remote"]:
                    try:
                        val["plugin_controller"].shutdown(_pyroTimeout=1)
                    except:
                        # its a bit late here for catching errors....
                        pass
            # api_keys = list(loader.consumer_api.keys())
            # for i in api_keys:
            #     del loader.consumer_api[i]
            # gc.collect()
            try:
                loader.pyro_daemon.close()
            except:
                pass
            print("Server has been shut down correctly")
            if signum:
                signal.default_int_handler(signum, frame)
            # exit()


class CountingThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    def __init__(self, max_workers=None, *args, **kwargs):
        super().__init__(max_workers, *args, **kwargs)
        self._active_tasks = set()
        self.max_task_count = max_workers

    def submit(self, fn, *args, **kwargs):
        future = super().submit(fn, *args, **kwargs)
        self._active_tasks.add(future)
        future.add_done_callback(self._task_completed)
        return future

    def _task_completed(self, future):
        self._active_tasks.remove(future)

    def get_active_task_count(self):
        return len(self._active_tasks)

    def get_free_worker_count(self):
        return self._max_workers - len(self._active_tasks)


class ThreadSafeCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.count += 1

    def decrement(self):
        with self.lock:
            self.count -= 1

    def get_count(self):
        # with self.lock:
        return self.count
