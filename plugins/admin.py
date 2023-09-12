import json

import pandas
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path, re_path
from plugins.plugin_manager import public_variables
import psutil
import pandas as pd
from django.http import HttpResponseNotFound
import pprint
process = psutil.Process()
import datetime

class PluginAdmin(admin.AdminSite):
    # index_template = "custom_index"

    def get_urls(self):
        urls = [path("plugin_management/", self.admin_view(self.plugin_manager_page),
                     name="plugin_management", ),
                re_path("^plugin/", self.admin_view(self.plugin_page),
                        name="plugin", ),
                ] + super().get_urls()
        return urls

    def plugin_page(self, request):
        name = request.path.split("/plugin/")[1]
        if name in public_variables["loaded_plugins"]:
            loaded = True
            info = public_variables["loaded_plugins"][name]
            add_info = public_variables["found_plugins"][name]
        elif name in public_variables["found_plugins"]:
            loaded = False
            info = public_variables["found_plugins"][name]
        else:
            return HttpResponseNotFound("No such plugin")


        excluded = ["plugin_controller", "callables", "local_code", "full_module"]
        dic = {i: [info[i]] for i in info if i not in excluded}
        if "callables" in info:
            dic["functions"] = "<br>".join([str(i) for i in info["callables"]])
            dic.update({i: [add_info[i]] for i in add_info if i not in excluded})
        # pp(dic["config"], indent=2)
        plug_conf = dic["config"][0]
        if plug_conf == None:
            dic["config"] = ["No config"]
        else:
            dic["config"] = ["<br>".join([i +" : " + str(plug_conf[i])[:min(90,len(str(plug_conf[i])))] for i in plug_conf])]
        if "callable_info" in dic:
            arr = []
            for i in dic["callable_info"]:
                arr.append("<p>"+pprint.pformat(i, indent=2, width=200).replace("\n","<br>")+"</p>")
            dic["callable_info"] = ["<br>".join(arr).replace(" ", "&nbsp;")]
        df = pd.DataFrame(dic)
        table_html = df.T.to_html(justify="left", escape=False)
        context = {
            "text": "Hello Admin",
            "page_name": "Plugin",
            "app_list": self.get_app_list(request),
            **self.each_context(request),
            "info_table": table_html,
            "is_loaded": str(loaded),
            "name": name
        }
        return TemplateResponse(request, "admin/plugin.html", context)

    def plugin_manager_page(self, request):
        free_tasks = public_variables["task_threadpool"].get_free_worker_count()
        max_tasks = public_variables["task_threadpool"].max_task_count
        with process.oneshot():
            conns = ""
            for i in process.connections():
                addr = i.laddr
                if addr.ip == "127.0.0.1":
                    ip = "local"
                else:
                    ip = addr.ip
                conns += f"IP: {ip} Port {addr.port};"
            p_time = (datetime.datetime.now()-datetime.datetime.fromtimestamp(process.create_time())).total_seconds()
            tot_cpu_time = process.cpu_times()[0] #+ process.cpu_times()[1]
            # print(p_time, tot_cpu_time)
            vals = [["Active concurrent users", public_variables["active_user_connections"].get_count()],
                    ["Available tasks", str(free_tasks) + "/" + str(max_tasks)],
                    ["Used threads", process.num_threads()],
                    ["Used (real) memory for server in MB", round(process.memory_info()[0] / 1024 ** 2)],
                    ["Open connections", conns],
                    ["Total CPU time in s", tot_cpu_time],
                    ["Prop. CPU time single core in %", f"{tot_cpu_time*100/p_time:.4f}"]]

        transpose = [[row[i] for row in vals] for i in range(len(vals[0]))]
        proc_df = pandas.DataFrame({"Type": transpose[0], "Value": transpose[1]})
        table_html = proc_df.to_html(justify="left", index=False)

        active_plugins = list(public_variables["loaded_plugins"].keys())
        all_available_plugins = list(public_variables["found_plugins"].keys())

        # plugin_table = pd.DataFrame

        context = {
            "text": "Hello Admin",
            "page_name": "Plugin management",
            "app_list": self.get_app_list(request),
            **self.each_context(request),
            "active_connections": public_variables["active_user_connections"].get_count(),
            "info_table": table_html,
            "active_plugins": active_plugins,
            "available_plugins": all_available_plugins
        }
        return TemplateResponse(request, "admin/plugin_manager.html", context)
