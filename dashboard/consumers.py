# chat/consumers.py
import asyncio
import json
import os.path
import threading

from channels.generic.websocket import AsyncWebsocketConsumer
import logging
import re
from plugins.plugin_manager import _PluginLoader, public_variables
from django.conf import settings
import collections
import datetime
import plugins.conf

logger = logging.getLogger()
user_logger = logging.getLogger("ws_handler")


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # if not self.scope["user"].is_anonymous:
        await self.accept()
        self.api = _PluginLoader.register_consumer(self.channel_name, self)

        # await _PluginLoader.execute_command("--help", self.channel_name)

        user_logger.info("User connected")
        self.task_deque = collections.deque(maxlen=settings.MAX_USER_JOBS)
        if settings.NLP_BACKEND == "none":
            await self.send(
                text_data=json.dumps({"role": "server", "content": "Warning: No NLP backend defined. "
                                                                   + datetime.datetime.now().strftime("%H:%M:%S")}))
        else:
            self.original_nlp_backend = settings.NLP_BACKEND

            await self.send(
                text_data=json.dumps(
                    {"update_conversation": await self.api.get_conv_tracker(to_openai=False, exlude_key="hidden")}))

        public_variables["active_user_connections"].increment()

        found = False
        for entry in plugins.conf.all_available_functions:
            if entry.get('name') ==  "data__user-init":
                found = True
                break
        if found:
            await self.api.call_plugin_function("data", "user_init")

    async def disconnect(self, close_code):
        _PluginLoader.unregister_consumer(self.channel_name)
        public_variables["active_user_connections"].decrement()

    async def try_add_task(self, task):
        finished = set()
        for i in self.task_deque:
            if i.done():
                finished.add(i)
        for i in finished:
            self.task_deque.remove(i)
            del i
        if len(self.task_deque) < self.task_deque.maxlen:
            new_task = asyncio.create_task(task)
            self.task_deque.append(new_task)
            # await new_task
        else:
            await self.send(text_data=json.dumps(
                {"role": "status", "content": f"Exceeded maximum concurrect requests<br>Max: {self.task_deque.maxlen}",
                 "timeout": 10000,
                 "level": "danger"}))

    async def collect_tasks(self):
        finished = set()
        for i in self.task_deque:
            if i.done():
                finished.add(i)
        for i in finished:
            ex = i.exception()
            if ex:
                print(ex)
            self.task_deque.remove(i)
            del i

    async def receive(self, text_data, bytes_data=None):
        client_payload = json.loads(text_data)
        # user_logger.debug(f"Received payload: {client_payload}")
        if "CMD" in client_payload and client_payload["CMD"] == "function_call":
            api_obj = _PluginLoader.singleton.consumer_api[self.channel_name]
            await self.try_add_task(
                api_obj.call_plugin_function(plugin_name=client_payload["plugin_name"],
                                             function_name=client_payload["function_name"],
                                             args=tuple(client_payload["args"]),
                                             kwargs=client_payload["kwargs"] if "kwargs" in client_payload else {
                                             }
                                             , user_inited=True,
                                             oneway=True))
        elif "CMD" in client_payload and client_payload["CMD"] == "clear_tracker":
            await self.api.clear_conversations()
            await self.api.rebuild_conv_tracker()
            # await self.send(text_data=json.dumps(
            #         {"update_conversation": await self.api.get_conv_tracker(to_openai=False, exlude_key="hidden")}))
        if "content" in client_payload:
            cmds = re.findall(r"##(.*?)#", client_payload["content"])
            if len(cmds) != 0:
                if cmds[0] == "disable_nlp":
                    settings.NLP_BACKEND = "none"
                    await self.send(text_data=json.dumps({"role": "server", "content": "NLP processing disabled"}))

                elif cmds[0] == "enable_nlp":
                    settings.NLP_BACKEND = self.original_nlp_backend
                    await self.send(text_data=json.dumps({"role": "server", "content": "NLP processing enabled"}))
                elif cmds[0] == "collect_tasks":
                    await self.collect_tasks()
                else:
                    user_logger.debug(f"Command execution requested for : {cmds}")
                    for i in cmds:
                        await self.try_add_task(_PluginLoader.execute_command(i, self.channel_name))
            elif settings.NLP_BACKEND != "none" and not settings.DISABLE_CHAT:
                user_logger.debug(f"LLM response requested for: {client_payload}")
                await self.try_add_task(_PluginLoader.call_nlp_model(client_payload, self.channel_name))

        # MiddleWare.user_receive_payload(self, client_payload)
        #
        # if "cmd" in client_payload:
        #     try:
        #         parser_entry(client_payload, self)
        #     except Exception as e:
        #         logger.error(f"Command parser has failed unrecoverably!\n{e}")
        #
        # if "message" in client_payload:
        #     LoadedPlugins.conversation_backend.get_answer(client_payload)

        # only sync
        # self.scope["session"].save()
