import math

import rixaplugin.internal.api as plugin_api
import json

from channels.db import database_sync_to_async
from pyalm import ConversationTracker
import markdown2
# class ChannelsAPI(plugin_api.BaseAPI):
#     def __init__(self):
#

import logging

from asgiref.sync import sync_to_async, async_to_sync

logger = logging.getLogger("ServerAPI")

class ChannelBridgeAPI(plugin_api.BaseAPI):
    """
    A translation layer between the plugin API and the channel layer

    Picks up calls that should not go to the consumer (e.g. log calls).
    The instantiated objects of this class usually do not reside in the same process as the websocket consumer.
    """

    def __init__(self, channel_layer, channel_name,):
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
                                                 }
        self.chat_modes = chat_modes
        # self.selected_chat = self.scope["session"]["settings"]["selected_chat"]
        # self.chat_mode = self.scope["session"]["settings"]["selected_chat_mode"]

        # tracker = ConversationTracker.from_yaml(example_chat)
        # self.scope["session"]["chat_histories"] = [tracker.to_yaml()]

    def get_system_msg(self):
        return self.chat_modes[self.selected_chat_mode]["system_msg"]

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
        return self.scope["session"]["settings"]["selected_chat"]

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

    async def update_and_display_tracker_entry(self, tracker_yaml):
        self.scope["session"]["chat_histories"][self.selected_chat] = tracker_yaml
        tracker = ConversationTracker.from_yaml(tracker_yaml)
        # from pprint import pp
        # print("----------------")
        # pp(tracker.tracker, width=150)
        # print("---------------")
        assistant_msg = tracker[-1]
        await sync_to_async(self.consumer.scope["session"].save)()
        await self.display_in_chat(tracker_entry=assistant_msg, flags="enable_chat")

    async def add_tracker_entry(self, role, content, metadata=None, function_calls=None, feedback=None, sentiment=None, add_keys=None):
        tracker = ConversationTracker()
        tracker.load_from_yaml(self.scope["session"]["chat_histories"][-1], is_file=False)
        tracker.add_entry(content, role, metadata, function_calls, feedback, sentiment, add_keys)
        self.scope["session"]["chat_histories"][-1] = tracker.to_yaml()

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

    async def show_message(self, message, timeout=5000, theme="info"):
        # Generated from ../rixawebserver/dashboard/static/dashboard/bot_gui/js/script.js:5
        return await self.consumer.send(
            text_data=json.dumps({"function": "showMessage", "type": "f_call", "arguments": [message, timeout, theme]}))

    async def send_custom_message(self, message):
        await self.consumer.send(text_data=json.dumps(message))

    async def display(self, html=None, json_str=None, plotly_obj=None, text=None, auto_place=True, place_index=-1,
                      size=5):
        if html:
            html = html.replace("\\n", "<br>")
            html = html.replace("\\t", "&nbsp;")
            await self.consumer.send(text_data=json.dumps(
                {"role": "HTML", "content": html, "forced_position": not auto_place}))
        elif plotly_obj:
            plotly_html = plotly_obj.to_html(include_plotlyjs=False, include_mathjax=False, full_html=False)
            await self.consumer.send(
                text_data=json.dumps({"role": "HTML", "content": plotly_html, "forced_position": not auto_place}))
        elif json_str:
            await self.consumer.send(text_data=json.dumps({"role": "JSON", "content": json_str}))
        elif text:
            await self.consumer.send(text_data=json.dumps(
                {"role": "HTML", "content": f"<p>{text}</p>", "forced_position": not auto_place}))
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
            raise Exception("No valid object specified for displaying!")

