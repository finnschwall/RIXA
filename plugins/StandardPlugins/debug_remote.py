import threading

import click
import time
from plugins.api import *

@plugin_init(name="debug_remote", hidden_in_function_dic=True, help="Remote debugging stuff")
def debug_remote(ctx, config, meta_config):
    pass

@debug_remote.plugin_method()
def test():
    print("hey")

@debug_remote.plugin_method()
@argument("to_print")
def print_to_chat(api, to_print):
    api.display_in_chat(to_print)
    api.call_remote("debug","print",(),{})

@debug_remote.plugin_method()
@argument("to_print")
def raise_exception(api, to_print):
    raise Exception(to_print)


@debug_remote.plugin_method()
@argument("content", type=str)
def write_to_html(api, content):
    api.display_html(content)


@debug_remote.plugin_method()
@argument("tts", type=int)
def halt_server(api, tts):
    api.display_message(f"Waiting for {tts}")
    time.sleep(tts)
    api.display_message(f"Finished waiting")
