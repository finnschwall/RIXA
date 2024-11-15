import math
from datetime import time

import rixaplugin.internal.api as plugin_api
import json

from channels.db import database_sync_to_async
from pyalm import ConversationTracker
# class ChannelsAPI(plugin_api.BaseAPI):
#     def __init__(self):
#

import logging
from rixaplugin import _memory
from asgiref.sync import sync_to_async, async_to_sync

from RIXAWebserver import settings

logger = logging.getLogger("ServerAPI")

class ChannelBridgeAPI(plugin_api.BaseAPI):
    """
    A translation layer between the plugin API and the channel layer

    Picks up calls that should not go to the consumer (e.g. log calls).
    The instantiated objects of this class usually do not reside in the same process as the websocket consumer.
    """

    def __init__(self, channel_layer, channel_name, request_id=-1, identity=None, scope=None, plugin_variables={}):
        # call the parent constructor
        super().__init__(request_id, identity, scope)
        self.plugin_variables = plugin_variables
        self.channel_layer = channel_layer
        self.channel_name = channel_name
        self.is_remote = False
        self.request_id = -1

    async def send_message(self, func_name, args, kwargs):
        # This function sends a message to the channel layer
        await self.channel_layer.send(
            self.channel_name,
            {
                "type": "api.dispatcher",
                "api_function_destination": func_name,
                "args": args,
                "kwargs": kwargs
            }
        )

    async def display(self, *args, **kwargs):
        await self.send_message("display", args, kwargs)

    async def display_in_chat(self, *args, **kwargs):
        await self.send_message("display_in_chat", args, kwargs)

    async def show_message(self, *args, **kwargs):
        await self.send_message("show_message", args, kwargs)

    async def update_and_display_tracker_entry(self, *args, **kwargs):
        await self.send_message("update_and_display_tracker_entry", args, kwargs)


class ConsumerAPI(plugin_api.BaseAPI):
    total_tokens = 0
    def __init__(self, consumer=None, chat_modes=None):
        self.consumer = consumer
        self.scope = consumer.scope
        if not self.scope["session"].get("chat_histories"):
            tracker = ConversationTracker()
            self.scope["session"]["chat_histories"] = [tracker.to_yaml()]
        if not self.scope["session"].get("settings"):
            self.scope["session"]["settings"] = {"selected_chat": 0,
                                                 "selected_chat_mode": "default",
                                                 "enable_function_calls": True,
                                                 "enable_knowledge_retrieval": True,
                                                 "current_chat_id": self.generate_chat_id()
                                                 }
        if not self.scope["session"].get("plugin_variables"):
            self.scope["session"]["plugin_variables"] = {}
        self.chat_modes = chat_modes

    def generate_chat_id(self):
        from datetime import datetime
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        return self.scope["user"].username + time_str

    def update_plugin_variable(self, plugin_id, setting_id, value):
        plugin_settings = _memory.get_all_variables()
        if plugin_id not in plugin_settings:
            raise ValueError(f"Plugin '{plugin_id}' does not exist")
        if setting_id not in plugin_settings[plugin_id]:
            raise ValueError(f"Setting '{setting_id}' does not exist for plugin '{plugin_id}'")
        type_mapping = {
            'int': int,
            'float': float,
            'str': str,
            'bool': bool
        }
        if "type" in plugin_settings[plugin_id][setting_id] and plugin_settings[plugin_id][setting_id]["type"] in type_mapping:
            if type(value) != type_mapping[plugin_settings[plugin_id][setting_id]["type"]]:
                raise ValueError(f"Setting '{setting_id}' for plugin '{plugin_id}' must be of type {plugin_settings[plugin_id][setting_id]['type']}")
            # raise ValueError(f"Setting '{setting_id}' for plugin '{plugin_id}' must be of type {plugin_settings[plugin_id][setting_id]['type']}")
        if "options" in plugin_settings[plugin_id][setting_id] and plugin_settings[plugin_id][setting_id]["options"] and\
                value not in plugin_settings[plugin_id][setting_id]["options"]:
            raise ValueError(f"Setting '{setting_id}' for plugin '{plugin_id}' must be one of the following options: {plugin_settings[plugin_id][setting_id]['options']}")

        if plugin_id not in self.scope["session"]["plugin_variables"]:
            self.scope["session"]["plugin_variables"][plugin_id] = {setting_id: value}
        else:
            self.scope["session"]["plugin_variables"][plugin_id][setting_id] = value

    def get_plugin_variables(self):
        return self.scope["session"]["plugin_variables"]


    def get_system_msg(self):
        return self.chat_modes[self.selected_chat_mode]["system_msg"]

    def get_first_message(self):
        return self.chat_modes[self.selected_chat_mode]["first_message"]

    def is_knowledge_enabled(self):
        return self.enable_knowledge_retrieval and self.chat_modes[self.selected_chat_mode]["use_document_retrieval"]

    def get_knowledge_retrieval_domain(self):
        return self.chat_modes[self.selected_chat_mode]["document_tags"]

    def is_function_calls_enabled(self):
        return self.enable_function_calls and self.chat_modes[self.selected_chat_mode]["use_function_calls"]

    def get_current_tags(self):
        return self.chat_modes[self.selected_chat_mode]["tags"]

    def get_current_plugins(self):
        return self.chat_modes[self.selected_chat_mode]["plugins"]


    @property
    def selected_chat_mode(self):
        return self.scope["session"]["settings"]["selected_chat_mode"]

    @selected_chat_mode.setter
    def selected_chat_mode(self, value):
        if value in self.chat_modes.keys():
            self.scope["session"]["settings"]["selected_chat_mode"] = value
        else:
            raise ValueError(f"Chat mode '{value}' is not available for this user")

    @property
    def selected_chat(self):
        return 0
        # return self.scope["session"]["settings"]["selected_chat"]

    @selected_chat.setter
    def selected_chat(self, value):
        self.scope["session"]["settings"]["selected_chat"] = value

    @property
    def enable_function_calls(self):
        return self.scope["session"]["settings"]["enable_function_calls"]

    @enable_function_calls.setter
    def enable_function_calls(self, value):
        self.scope["session"]["settings"]["enable_function_calls"] = bool(value)

    @property
    def enable_knowledge_retrieval(self):
        return self.scope["session"]["settings"]["enable_knowledge_retrieval"]

    @enable_knowledge_retrieval.setter
    def enable_knowledge_retrieval(self, value):
        self.scope["session"]["settings"]["enable_knowledge_retrieval"] = bool(value)

    def delete_current_tracker(self):
        tracker = ConversationTracker()
        self.scope["session"]["chat_histories"][self.selected_chat] = tracker.to_yaml()


    def get_active_conversation(self):
        tracker_yaml = self.scope["session"]["chat_histories"][self.selected_chat]
        tracker = ConversationTracker.from_yaml(tracker_yaml)
        return tracker

    async def set_tracker(self, tracker_yaml):
        tracker = ConversationTracker.from_yaml(tracker_yaml)
        self.scope["session"]["chat_histories"][self.selected_chat] = tracker_yaml
        for i in tracker:
            await self.display_in_chat(tracker_entry=i, flags="enable_chat")
        await sync_to_async(self.consumer.scope["session"].save)()


    async def update_and_display_tracker_entry(self, tracker_yaml):
        self.scope["session"]["chat_histories"][self.selected_chat] = tracker_yaml
        tracker = ConversationTracker.from_yaml(tracker_yaml)
        assistant_msg = tracker[-1]
        # await sync_to_async(self.consumer.scope["session"].save)()
        ConsumerAPI.total_tokens += assistant_msg["metadata"].get("total_tokens", 0)
        await self.write_chat_to_db(tracker_yaml, tracker)
        await self.display_in_chat(tracker_entry=assistant_msg, flags="enable_chat")

    @database_sync_to_async
    def write_chat_to_db(self, tracker_yaml, tracker):
        from .models import Conversation
        self.consumer.scope["session"].save()

        chat = Conversation.objects.update_or_create(id=self.scope["session"]["settings"]["current_chat_id"],
        defaults={"user":self.scope["user"], "tracker_yaml":tracker_yaml,"model_name":tracker.metadata.get("model_name","UNKNOWN")})
        # chat.save()

    async def new_chat(self):
        #delete tracker and create a new one. Add directly the first message if it exists
        self.scope["session"]["settings"]["current_chat_id"] = self.generate_chat_id()
        tracker = ConversationTracker()
        if self.get_first_message():
            tracker.add_entry(self.get_first_message(), "assistant")
        self.scope["session"]["chat_histories"] = [tracker.to_yaml()]
        await sync_to_async(self.consumer.scope["session"].save)()

    async def add_tracker_entry(self, role, content, metadata=None, function_calls=None, feedback=None, sentiment=None, add_keys=None):
        tracker = ConversationTracker()
        tracker.load_from_yaml(self.scope["session"]["chat_histories"][-1], is_file=False)
        tracker.add_entry(content, role, metadata, function_calls, feedback, sentiment, add_keys)
        tracker_yaml = tracker.to_yaml()
        self.scope["session"]["chat_histories"][-1] = tracker_yaml



    async def clear_conversations(self):
        tracker = ConversationTracker()
        self.scope["session"]["chat_histories"] = [tracker.save_to_yaml()]

    async def save_usr_obj(self, key, val, expires="never"):
        self.scope["session"]["plugin_memory"][key] = val

    async def test_message(self,*args,**kwargs):
        print(args)
        print(kwargs)

    async def retrieve_usr_obj(self, key):
        if key in self._scope["session"]["plugin_memory"]:
            return self._scope["session"]["plugin_memory"][key]
        else:
            raise IndexError(f"'{key}' does not exist in the storage for this user")

    async def sync_session_storage_db(self):
        await sync_to_async(self.scope["session"].save)()

    async def show_message(self, message,  theme="info", timeout=5000):
        # Generated from ../rixawebserver/dashboard/static/dashboard/bot_gui/js/script.js:5
        return await self.consumer.send(
            text_data=json.dumps({"function": "showMessage", "type": "f_call", "arguments": [message, timeout, theme]}))

    async def send_custom_message(self, message):
        await self.consumer.send(text_data=json.dumps(message))

    async def display(self, html=None, json_str=None, plotly_obj=None, text=None, custom_msg =None):
        if html:
            html = html.replace("\\n", "<br>")
            html = html.replace("\\t", "&nbsp;")
            await self.consumer.send(text_data=json.dumps(
                {"role": "HTML", "content": html}))
        elif plotly_obj:
            plotly_html = plotly_obj.to_html(include_plotlyjs=False, include_mathjax=False, full_html=False)
            await self.consumer.send(
                text_data=json.dumps({"role": "HTML", "content": plotly_html}))
        elif json_str:
            await self.consumer.send(text_data=json.dumps({"role": "JSON", "content": json_str}))
        elif text:
            await self.consumer.send(text_data=json.dumps(
                {"role": "HTML", "content": f"<p>{text}</p>"}))
        elif custom_msg:
            if settings.DEBUG or True:
                await self.consumer.send(text_data=custom_msg)
            else:
                logger.error("Custom messages are only allowed in debug mode")
        else:
            raise Exception("No valid object specified for displaying!")

    async def display_in_chat(self,tracker_entry=None, text=None, html=None, plotly_obj=None,
                              role="assistant", citations=None, index=-1,flags=None):
        data = {}
        if flags:
            if type(flags) is not list:
                flags = [flags]
            data["flags"] = flags
        if tracker_entry:
            data["role"] = "tracker_entry"
            tracker_entry["role"] = str(tracker_entry["role"]).lower()
            data["tracker"] = tracker_entry
            await self.consumer.send(text_data=json.dumps(data, ensure_ascii=True))
        elif html:
            html = html.replace("\\n", "<br>")
            html = html.replace("\\t", "&nbsp;")
            # TODO make this actually display in the chat
            data.update({"role": "assistant", "content": html, "forced_position": False})
            await self.consumer.send(text_data=json.dumps(data))
            # await self.consumer.send(text_data=json.dumps({"role": "HTML", "content": html, "location": "inline"}))
        elif plotly_obj:
            plotly_html = plotly_obj#plotly_obj.to_html(include_plotlyjs=False, include_mathjax=False, full_html=False)
            await self.consumer.send(
                text_data=json.dumps({"role": "HTML", "content": plotly_html, "location": "inline"}))
        elif text:
            data.update({"role": role, "content": f"{text}", "forced_position": False, "index": index, "citations": citations if citations else ""})
            await self.consumer.send(text_data=json.dumps(data, ensure_ascii=True))
        else:
            await self.consumer.send(text_data=json.dumps({"role":role, "content": "Warning: An API call was made to display something in the chat. However no content was supplied."}, ensure_ascii=True))

