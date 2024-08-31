# chat/consumers.py
import asyncio
import base64
import json
import os
import pprint
import threading
from datetime import datetime

from asgiref.sync import sync_to_async
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
import re

from django.contrib.auth import get_user_model

from RIXAWebserver import settings
from account_managment.visit_statistics import SessionStatistics

from .api import ChannelBridgeAPI, ConsumerAPI
from .models import PluginScope, ChatConfiguration

logger = logging.getLogger()
user_logger = logging.getLogger("rixa.ws_handler")

connection_lock = threading.Lock()


class ChatConsumer(AsyncWebsocketConsumer):
    active_connections = 0

    async def connect(self):
        await self.accept()
        chat_modes = await self.get_user_info()

        self.consumer_api = ConsumerAPI(self, chat_modes)

        for i in self.consumer_api.get_active_conversation():
            await self.consumer_api.display_in_chat(tracker_entry=i)

        with connection_lock:
            ChatConsumer.active_connections += 1
        self.msg_count = 0
        self.start_time = datetime.now()

    @database_sync_to_async
    def get_user_info(self):
        if not self.scope["user"].is_authenticated:
            return
        chat_config = self.scope["user"].rixauser.configurations_read.all()
        chat_config = set(chat_config)
        globally_available_configs = set(ChatConfiguration.objects.filter(available_to_all=True))
        chat_config = chat_config.union(globally_available_configs)
        chat_config = list(chat_config)

        chat_modes = {}
        for config in chat_config:
            entry = {"use_document_retrieval": config.use_document_retrieval, "document_tags": config.document_tags,
                     "plugins": config.included_plugins, "use_function_calls": config.use_function_calls,
                     "tags": list(config.included_scopes.all().values_list('name', flat=True)),
                     "system_msg": config.system_message,
                     "first_message": config.first_message if config.first_message != "" else None}

            chat_modes[config.name] = entry
            # plugins_in_chat_mode[config.name] = config.included_plugins#[i.included_plugins for i in config.included_plugins]
        # tags_in_chat_mode = {}
        # for config in chat_config:
        #     tags_in_chat_mode[config.name] = list(config.included_scopes.all().values_list('name', flat=True))
        return chat_modes


    async def api_dispatcher(self, event):
        """
        Dispatches events to the correct function based on the
        'api_function_destination' key in the event dictionary.
        """
        function_name = event.pop('api_function_destination', None)
        if function_name and hasattr(self.consumer_api, function_name):
            function_to_call = getattr(self.consumer_api, function_name)
            if callable(function_to_call):
                event.pop('type', None)
                func_args = event.pop('args', [])
                func_kwargs = event.pop('kwargs', {})
                await function_to_call(*func_args, **func_kwargs)
            else:
                raise TypeError(f"The API call '{function_name}' is not callable.")
        else:
            raise AttributeError(f"'{function_name}' is not a valid Consumer API function.")

    async def disconnect(self, close_code):
        with connection_lock:
            ChatConsumer.active_connections -= 1
        await self.write_to_user()

    @database_sync_to_async
    def write_to_user(self):
        if not self.scope["user"].is_authenticated:
            return
        try:
            self.scope["user"].rixauser.total_messages += self.msg_count
            self.scope["user"].rixauser.total_time_spent += (datetime.now() - self.start_time).seconds//60
            self.scope["user"].rixauser.total_sessions += 1
            messages_per_session_json = json.loads(self.scope["user"].rixauser.messages_per_session) if self.scope["user"].rixauser.messages_per_session else []
            messages_per_session_json.append(self.msg_count)
            self.scope["user"].rixauser.messages_per_session = json.dumps(messages_per_session_json)
            self.scope["user"].rixauser.save()

            SessionStatistics.register_infos(self.scope["user"].username, self.msg_count, (datetime.now() - self.start_time).seconds//60)
        except Exception as e:
            user_logger.exception("Error while writing user info")
            print(e)


    async def websocket_receive(self, message):
        # print(self.scope["user"].get_user_permissions())
        message = json.loads(message["text"])
        req_type = message["type"]

        if req_type == "execute_plugin_code":

            await self.channel_layer.send(
                "plugin_interface",
                {
                    "type": "execute_plugin_code",
                    "channel_name": self.channel_name,
                    "code": message["content"],
                    "tags": self.consumer_api.get_current_tags(),
                    "allowed_plugins": self.consumer_api.get_current_plugins() ,
                    "plugin_variables": self.consumer_api.get_plugin_variables(),
                }
            )
        elif req_type == "call_plugin_function":

            await self.channel_layer.send(
                "plugin_interface",
                {
                    "type": "call_plugin_function",
                    "channel_name": self.channel_name,
                    "function_name": message["function_name"],
                    "tags": self.consumer_api.get_current_tags(),
                    "allowed_plugins": self.consumer_api.get_current_plugins(),
                    "plugin_variables": self.consumer_api.get_plugin_variables(),
                    "args" : message.get("args", []),
                    "kwargs": message.get("kwargs", {}),
                }

            )
        elif req_type == "usr_msg":
            self.msg_count += 1
            tracker = self.consumer_api.get_active_conversation()
            tracker.add_entry(message["content"], "user")

            msg = {
                    "type": "generate_response",
                    "channel_name": self.channel_name,
                    "args": (tracker.to_yaml(),),
                    "tags": self.consumer_api.get_current_tags(),
                    "allowed_plugins": self.consumer_api.get_current_plugins(),
                "plugin_variables": self.consumer_api.get_plugin_variables(),
                    "kwargs": {"enable_function_calling": self.consumer_api.is_function_calls_enabled(),
                               "enable_knowledge_retrieval": self.consumer_api.is_knowledge_enabled(),
                                "knowledge_retrieval_domain" : self.consumer_api.get_knowledge_retrieval_domain(),
                               "username": self.scope["user"].username, "system_msg": self.consumer_api.get_system_msg()
                               }
                }
            await self.channel_layer.send(
                "plugin_interface",
                msg
            )
        elif req_type == "change_setting":
            try:
                if message["setting"] == "enable_function_calls":
                    self.consumer_api.enable_function_calls = message["value"]
                if message["setting"] == "enable_knowledge_retrieval":
                    self.consumer_api.enable_knowledge_retrieval = message["value"]
                if message["setting"] == "selected_chat_mode":
                    self.consumer_api.selected_chat_mode = message["value"]
                    await self.consumer_api.new_chat()
                    for i in self.consumer_api.get_active_conversation():
                        await self.consumer_api.display_in_chat(tracker_entry=i)

                await sync_to_async(self.scope["session"].save)()
            except Exception as e:
                user_logger.exception("Error while changing settings")
        elif req_type == "update_plugin_setting":
            try:
                plugin_id = message["plugin_id"]
                setting_id = message["setting_id"]
                value = message["value"]
                self.consumer_api.update_plugin_variable(plugin_id, setting_id, value)
                await sync_to_async(self.scope["session"].save)()
            except Exception as e:
                user_logger.exception(f"USER {self.scope['user'].username}: Error while changing plugin settings")
                await self.consumer_api.show_message(str(e), theme="error")
        elif req_type == "bug_report":

            try:
                from dashboard import views
                if get_folder_size(settings.WORKING_DIRECTORY + "/bug_reports") > 200:
                    raise Exception("Bug report folder is too large")
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                report = message.pop("report")
                current_conv_tracker = self.consumer_api.get_active_conversation().to_yaml()
                username = self.scope["user"].username
                headers = self.scope["headers"]
                client = self.scope.get("client", "no client info")
                user_settings = self.scope["session"].get("settings", "no settings available")
                with open(settings.WORKING_DIRECTORY + f"/bug_reports/{username}_{current_time}.txt", "w") as f:
                    total_text = f"Bugreport submitted by {username} at {current_time}\n\n"
                    total_text += f"Report:\n-----\n{report}\n-----\n\n"
                    total_text += f"Webserver date: {datetime.fromtimestamp(views.latest_time).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    total_text += f"Client connection: {client}\n"
                    total_text += f"User settings:\n{pprint.pformat(user_settings, indent=4)}"
                    total_text += f"\n\nConversation tracker:\n{current_conv_tracker}"
                    total_text += "\n\nAuxiliary info\n-----\n\n"
                    total_text += f"Headers:\n{pprint.pformat(headers, indent=4)}\n\n"
                    total_text += f"Client infos:\n{pprint.pformat(message, indent=4)}"
                    f.write(total_text)
                if "image" in message:
                    format, imgstr = message["image"].split(';base64,')
                    ext = format.split('/')[-1]
                    image = base64.b64decode(imgstr)
                    with open(settings.WORKING_DIRECTORY + f"/bug_reports/{username}_{current_time}.{ext}", "wb") as f:
                        f.write(image)
            except Exception as e:
                user_logger.exception("Error while submitting bug report")
                await self.consumer_api.show_message(f"USER {self.scope['user'].username}: Error while submitting bug report. This should not happen",
                                                     theme="error")

        elif req_type == "delete_current_tracker":
            # self.consumer_api.delete_current_tracker()
            await self.consumer_api.new_chat()
            for i in self.consumer_api.get_active_conversation():
                await self.consumer_api.display_in_chat(tracker_entry=i)
            await sync_to_async(self.scope["session"].save)()




def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)
