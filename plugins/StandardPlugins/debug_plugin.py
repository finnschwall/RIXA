import click
import time
import sys
from plugins.api import *
import json
from django.conf import settings

@plugin_init(name="debug", is_local=True, hidden_in_function_dic=False, help="General debugging stuff")
def data(ctx, config, meta_config):
    pass

@data.plugin_method(help="Immediately and irrecovably shuts down the entire plugin system. Server will no longer be functional after.")
async def shutdown(api):
    import plugins.plugin_manager
    plugins.plugin_manager._PluginLoader.shutdown_server()


@data.plugin_method()
@argument("to_print")
async def print_to_chat(api, to_print):
    await api.display_in_chat(to_print)


@data.plugin_method(help="Render all available backend relevant session data (e.g. cookies, username etc) as json")
async def show_json_session(api):
    session = json.dumps(dict(api.scope["session"]))
    await api.display_json(session)


@data.plugin_method(help="Renders arbitrary html code")
@argument("html_str")
async def write_to_html(api, html_str):
    await api.display_html(html_str)


@data.plugin_method()
@argument("time")
async def halt_server(api, time):
    await api.display_message(f"Waiting for {time}")
    time.sleep(time)
    await api.display_message(f"Finished waiting")

@data.plugin_method()
async def disable_nlp(api):
    settings.NLP_BACKEND = "none"
    await api.display_message("NLP processing disabled")

@data.plugin_method()
async def enable_nlp(api):
    settings.NLP_BACKEND = "chatgpt"
    await api.display_message("NLP processing enabled")