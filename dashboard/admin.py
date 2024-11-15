import json

import pandas
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, re_path
# from plugins.plugin_manager import public_variables
import psutil
import pandas as pd
from django.http import HttpResponseNotFound
import pprint

from dashboard.consumers import ChatConsumer
from dashboard.models import ChatConfiguration, PluginScope, Conversation

process = psutil.Process()
import datetime

from rixaplugin import _memory





class ChatConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name',)


class PluginScopeAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(PluginScope, PluginScopeAdmin)
admin.site.register(ChatConfiguration, ChatConfigurationAdmin)


class PluginAdmin(admin.AdminSite):
    def get_urls(self):
        urls = [path("plugin_management/", self.admin_view(self.plugin_manager_page),
                     name="plugin_management", ),
                re_path("^plugin/", self.admin_view(self.plugin_page),
                        name="plugin", ),
                ] + super().get_urls()
        return urls

    def plugin_page(self, request):
        name = request.path.split("/plugin/")[1]
        if name not in _memory.plugins:
            return HttpResponseNotFound("No such plugin")
        if request.method == "POST":
            if "remove_plugin" in request.POST:
                _memory.delete_plugin(name)
                messages.success(request, f"Plugin '{name}' removed")
            return redirect('admin:plugin_management')
        entry = _memory.plugins[name]
        table_html = _memory._pretty_print_plugin(entry).replace("\n", "<br>").replace(" ", "&nbsp;").replace("\t","&nbsp"*4)#pprint.pformat(entry, indent=4)
        context = {
            "text": "Hello Admin",
            "page_name": "Plugin",
            "app_list": self.get_app_list(request),
            **self.each_context(request),
            "info_table": table_html,
            "active": entry["is_alive"],
            "name": name
        }
        return TemplateResponse(request, "admin/plugin.html", context)

    def plugin_manager_page(self, request):
        free_tasks = _memory.executor.get_free_worker_count()
        max_tasks = _memory.executor.get_max_task_count()
        with process.oneshot():
            conns = len(process.connections())

            p_time = (datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time())).total_seconds()
            tot_cpu_time = process.cpu_times()[0]
            vals = [
                ["Available workers", str(free_tasks) + "/" + str(max_tasks)],
                ["Est. running tasks", _memory.tasks_in_system],
                    # ["Used threads", process.num_threads()],
                ["Used (real) memory for server in MB", round(process.memory_info()[0] / 1024 ** 2)],
                ["Total connections", conns],
                ["Consumer sockets (active users)", ChatConsumer.active_connections],
                ["Total CPU time in s", tot_cpu_time],
                ["Prop. CPU time single core in %", f"{tot_cpu_time * 100 / p_time:.1f}"]]

        transpose = [[row[i] for row in vals] for i in range(len(vals[0]))]
        proc_df = pandas.DataFrame({"Type": transpose[0], "Value": transpose[1]})
        table_html = proc_df.to_html(justify="left", index=False)

        active_plugins = {key: value for key, value in _memory.plugins.items() if value["is_alive"]}
        active_plugins = [{"id": i, "name": active_plugins[i]["name"],
                           "type": active_plugins[i]["type"], "tags": ','.join(active_plugins[i]["tags"])} for i in active_plugins]
        all_available_plugins = list({key: value for key, value in _memory.plugins.items() if not value["is_alive"]})



        context = {
            "text": "Hello Admin",
            "page_name": "Plugin management",
            "app_list": self.get_app_list(request),
            **self.each_context(request),
            "active_connections": 0,  # public_variables["active_user_connections"].get_count(),
            "info_table": table_html,
            "active_plugins": active_plugins,
            "offline_plugins": all_available_plugins
        }
        return TemplateResponse(request, "admin/plugin_manager.html", context)
