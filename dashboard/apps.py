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
import rixaplugin.data_structures.rixa_exceptions as rixa_exceptions
import rixaplugin.internal.rixalogger as rixalogger
from rixaplugin.internal.memory import _memory

loader_log = logging.getLogger("loader")
plugin_web_log = logging.getLogger("rixa.plugin_web")

def patch_users():
    """
    When creating users using the command line, the RixaUser object is not created. This function patches this.
    :return:
    """
    from account_managment.models import RixaUser
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all()
    for user in users:
        rixa_user, created = RixaUser.objects.get_or_create(user=user)
        if created:
            print(f"Created RixaUser for: {user.username}")


class DashboardConfig(AppConfig):
    """
    This class is the configuration class for the dashboard app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        from .admin import PluginAdmin
        from .models import ChatConfiguration
        admin.site.__class__ = PluginAdmin
        try:
            if not ChatConfiguration.objects.filter(name__exact="default").exists():
                ChatConfiguration.objects.create(name='default', available_to_all=True, )
            if settings.PATCH_USER_MODEL:
                patch_users()
        except Exception as e:
            loader_log.exception("Error while checking database consistency!")
        if len(sys.argv) > 1 and ("runserver" in sys.argv or 'RIXAWebserver.asgi:application' in sys.argv):
            if os.environ.get('RUN_MAIN') != 'true':
                loader_log.debug("Autoreloader started")
            else:
                pass
                # autor


original_set_event_loop = asyncio.set_event_loop


def patched_set_event_loop(loop):
    """
    This functions hooks into djangos main event loop to start the plugin system.
    It also starts a thread to collect statistics.
    :param loop:
    :return:
    """
    original_set_event_loop(loop)
    loop.create_task(plugin_interface())
    t = threading.Thread(name='collect_user_info', target=account_managment.visit_statistics.collect_user_info)
    t.daemon = True
    t.start()


asyncio.set_event_loop = patched_set_event_loop


async def await_code_execution(code, api_obj):
    """
    This function is used to execute code and then display the result in the chat.

    """
    try:
        fut = await rixaplugin.async_execute_code(code, api_obj=api_obj, return_future=True)
        ret_val = await fut
        disp_str = repr(ret_val)
        await api_obj.display_in_chat(html=disp_str[1:-1])
    except rixa_exceptions.RemoteException as e:
        await api_obj.display_in_chat(text=f"{e.traceback}")
    except Exception as e:
        err_str = rixalogger.format_exception(e, without_color=True)
        plugin_web_log.exception("Error in code execution")
        await api_obj.display_in_chat(text=f"```\n{err_str}\n```")


async def await_future_execution(future, api_obj, is_chat=False, suppres_return=False):
    """
    This function is used to await the result of a future and then display it in the chat or the web interface.
    Required as plugin execution is always async and the result must be awaited before it can be displayed.

    :param future:
    :param api_obj: api_obj of user (i.e. where to send the result)
    :param is_chat: Origin of future
    :return:
    """
    try:
        ret_val = await future
        if is_chat:
            if ret_val is None:
                await api_obj.display_in_chat(text="Unexpected error occurred", flags=["enable_chat"])
                return
            await api_obj.update_and_display_tracker_entry(ret_val)
            return
        if ret_val is None:
            return
        if suppres_return:
            return
        disp_str = "<code>" + repr(ret_val) + "</code>"
        await api_obj.display(html=disp_str)
    except Exception as e:
        plugin_web_log.exception("Error in future execution")
        tb = traceback.format_exc()
        err_str = repr(e).replace("\\n", "<br>")[-550:]
        await api_obj.display_in_chat(text=f"Oh no. Something has gone really wrong\n{err_str}")


async def plugin_interface():
    """
    This function listens to the channel layer for messages of type "plugin_interface" and then executes the
    corresponding plugin function or code.

    It is the "heart" of the plugin system.
    """
    channel_layer = get_channel_layer()
    from rixaplugin.test import introspection, test_api
    from pyalm.chat import alm_plugin

    import rixaplugin
    #rixaplugin.set_tags("catbot",["default"])
    rixaplugin.init_plugin_system(PMF.SERVER | PMF.THREAD | PMF.LOCAL, settings.NUM_SERVER_WORKER_THREADS, settings.DEBUG)
    while True:
        try:
            obj = await channel_layer.receive("plugin_interface")
            scope = {"inclusive_tags": obj["tags"], "included_plugins": obj["allowed_plugins"]}
            plugin_variables = obj["plugin_variables"]
            client_api= None

            if obj["type"] == "call_plugin_function":
                request_id = ChannelBridgeAPI.get_request_id(obj["function_name"], args = obj["args"], kwargs=obj["kwargs"])
                client_api = ChannelBridgeAPI(channel_layer, obj["channel_name"], request_id= request_id, scope=scope,
                                              plugin_variables=plugin_variables)
                future = await rixaplugin.async_execute(obj["function_name"], args=obj["args"], api_obj=client_api,
                                                        return_future=True)
                asyncio.create_task(await_future_execution(future, client_api, suppres_return=True))
            if obj["type"] == "execute_plugin_code":
                scope["force_include_plugin"] = ["introspection","knowledge_db", "test_api", "engine1"]
                client_api = ChannelBridgeAPI(channel_layer, obj["channel_name"], scope=scope,
                                              plugin_variables=plugin_variables)
                asyncio.create_task(await_code_execution(obj["code"][2:-1], client_api))
            if obj["type"] == "generate_response":
                request_id = ChannelBridgeAPI.get_request_id("generate_text", args=obj["args"],
                                                                        kwargs=obj["kwargs"])
                client_api = ChannelBridgeAPI(channel_layer, obj["channel_name"], request_id=request_id, scope=scope,
                                              plugin_variables=plugin_variables)
                future = await rixaplugin.async_execute("generate_text","alm_plugin", args=obj["args"], kwargs=obj["kwargs"],
                                                        api_obj=client_api, return_future=True)
                asyncio.create_task(await_future_execution(future, client_api, is_chat=True))
        except Exception as e:
            plugin_web_log.exception("Error in channel listener")
            tb = traceback.format_exc()
            err_str = repr(e).replace("\\n", "<br>")[-250:]
            await client_api.display_in_chat(text=f"Oh no. Something has gone really wrong\n{err_str}")
