import logging
import os
import sys
import threading

from django.apps import AppConfig
import rixaplugin
import asyncio
from channels.layers import get_channel_layer
import traceback
from django.contrib import admin
import account_managment

from .api import ChannelBridgeAPI, ConsumerAPI
from rixaplugin import PluginModeFlags as PMF
import asyncio
from django.conf import settings

loader_log = logging.getLogger("loader")
plugin_web_log = logging.getLogger("rixa.plugin_web")

def patch_users():
    from account_managment.models import RixaUser
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all()
    for user in users:
        rixa_user, created = RixaUser.objects.get_or_create(user=user)
        if created:
            print(f"Created RixaUser for: {user.username}")


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        from .admin import PluginAdmin
        admin.site.__class__ = PluginAdmin
        if settings.PATCH_USER_MODEL:
            patch_users()
        if len(sys.argv) > 1 and ("runserver" in sys.argv or 'RIXAWebserver.asgi:application' in sys.argv):
            if os.environ.get('RUN_MAIN') != 'true':
                loader_log.debug("Autoreloader started")
            else:
                pass
                # autor


original_set_event_loop = asyncio.set_event_loop


def patched_set_event_loop(loop):
    original_set_event_loop(loop)
    loop.create_task(plugin_interface())
    t = threading.Thread(name='collect_user_info', target=account_managment.visit_statistics.collect_user_info)
    t.daemon = True
    t.start()


asyncio.set_event_loop = patched_set_event_loop


async def await_code_execution(code, api_obj):
    try:
        fut = await rixaplugin.async_execute_code(code, api_obj=api_obj, return_future=True)
        ret_val = await fut
        disp_str = repr(ret_val)  # "<code>" +  + "</code>"
        await api_obj.display_in_chat(html=disp_str)
    except Exception as e:
        tb = traceback.format_exc()
        # exception_str = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
        err_str = "```\n"+tb[:-400]+"\n```"
        plugin_web_log.exception("Error in code execution")
        await api_obj.display_in_chat(text=f"{err_str}")


async def await_future_execution(future, api_obj, is_chat=False):
    try:
        ret_val = await future
        if is_chat:
            await api_obj.update_and_display_tracker_entry(ret_val)
            return
        disp_str = "<code>" + repr(ret_val) + "</code>"
        await api_obj.display(html=disp_str)
    except Exception as e:
        print(e)
        plugin_web_log.exception("Error in future execution")
        # print("exc")
        # raise e
        tb = traceback.format_exc()
        err_str = repr(e).replace("\\n", "<br>")[-250:]
        await api_obj.display_in_chat(text=f"Oh no. Something has gone really wrong\n{err_str}")


async def plugin_interface():
    channel_layer = get_channel_layer()
    from rixaplugin.test import introspection
    from rixaplugin.default_plugins import catbot
    import rixaplugin
    rixaplugin.set_tags("catbot",["cat"])
    rixaplugin.init_plugin_system(PMF.SERVER | PMF.THREAD | PMF.LOCAL, settings.NUM_WORKER_THREADS, settings.DEBUG)
    while True:
        try:
            obj = await channel_layer.receive("plugin_interface")
            client_api = ChannelBridgeAPI(channel_layer, obj["channel_name"])
            client_api.scope = {"inclusive_tags": obj["tags"], "included_plugins": obj["allowed_plugins"]}
            if obj["type"] == "call_plugin_function":
                future = await rixaplugin.async_execute(obj["function_name"], args=obj["args"], api_obj=client_api,
                                                        return_future=True)
                asyncio.create_task(await_future_execution(future, client_api))
            if obj["type"] == "execute_plugin_code":
                client_api.scope["force_include_plugin"] = ["introspection"]
                asyncio.create_task(await_code_execution(obj["code"][2:-1], client_api))
            if obj["type"] == "generate_response":

                future = await rixaplugin.async_execute("generate_text", args=obj["args"], kwargs=obj["kwargs"],
                                                        api_obj=client_api, return_future=True)
                asyncio.create_task(await_future_execution(future, client_api, is_chat=True))
        except Exception as e:
            plugin_web_log.exception("Error in channel listener")
            tb = traceback.format_exc()
            err_str = repr(e).replace("\\n", "<br>")[-250:]
            await client_api.display_in_chat(text=f"Oh no. Something has gone really wrong\n{err_str}")
