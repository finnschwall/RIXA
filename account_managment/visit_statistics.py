import math
import os
import threading
from datetime import datetime, timedelta
import time
import pandas as pd
import psutil
from django.conf import settings
from user_agents import parse
import re
from asgiref.sync import iscoroutinefunction, markcoroutinefunction
import numpy as np
import rixaplugin

from dashboard.api import ConsumerAPI


lock = threading.Lock()
max_between_time = timedelta(seconds=settings.STATISTICS_COLLECTION_INTERVAL)
# max_between_time = timedelta(minutes=0, seconds=10)
import subprocess as sp

def calculate_session_time(value):
    return (value.last_visited - value.first_visited).seconds//60


def process_user_agent(user_agent_str):
    user_agent = parse(user_agent_str)
    return user_agent.is_mobile, user_agent.browser.family, user_agent.is_touch_capable


def session_expired(user_info):
    return datetime.now() > user_info.last_visited + max_between_time

from dashboard.consumers import ChatConsumer
def collect_user_info():
    while True:
        time.sleep(max_between_time.seconds)
        # GPU Data
        tot_free_vrams = []
        tot_vrams = []
        performance_states = []
        gpu_utilizations = []
        gpu_names = []
        command = "nvidia-smi --query-gpu=memory.free,memory.total,pstate,utilization.gpu,gpu_name --format=csv"
        smi_info = sp.check_output(command.split()).decode('ascii').split('\n')[:-1][1:]
        for gpu_info in smi_info:
            tot_free_vram, tot_vram, performance_state, gpu_utilization, gpu_name = gpu_info.split(", ")
            performance_states.append(round((12 - int(performance_state[1:])) / 12 * 100))
            tot_free_vrams.append(int(tot_free_vram[:-4]))
            tot_vrams.append(int(tot_vram[:-4]))
            gpu_utilizations.append(int(gpu_utilization[:-1]))
            gpu_names.append(gpu_name)

        # CPU data
        vm = psutil.virtual_memory()
        ram_percent = vm.percent
        cpu_load_avg_1m, cpu_load_avg_5m, cpu_load_avg_15m = [round(i, 2) for i in psutil.getloadavg()]

        cur_ps = psutil.Process()
        with cur_ps.oneshot():
            proc_cpu_time_total = round(sum(cur_ps.cpu_times()), 3)
            proc_ram_usage = round(cur_ps.memory_info().rss / 1024 ** 2)
            p_time = (datetime.now() - datetime.fromtimestamp(cur_ps.create_time())).total_seconds()
            tot_cpu_time = cur_ps.cpu_times()[0]

        #network data
        net_io = psutil.net_io_counters()
        err_total = net_io.errin + net_io.errout
        total_mb_transmitted = (net_io.bytes_sent + net_io.bytes_recv)/(1024**2)


        #disk data
        disk_io = psutil.disk_io_counters()
        read_bytes = disk_io.read_bytes
        write_bytes = disk_io.write_bytes
        read_time = disk_io.read_time
        write_time = disk_io.write_time
        total_mb_disk = (disk_io.read_bytes + disk_io.write_bytes)/(1024**2)
        total_disk_time = (disk_io.read_time + disk_io.write_time)/1000

        # User/webserver data
        active_users = ChatConsumer.active_connections
        total_messages_sent = ChatConsumer.sent_messages

        ChatConsumer.sent_messages = 0
        total_tokens =ConsumerAPI.total_tokens
        ConsumerAPI.total_tokens = 0


        # Plugin data
        current_active_tasks = rixaplugin._memory.executor.get_active_task_count()
        max_tasks = rixaplugin._memory.executor.get_max_task_count()
        task_queue_count = rixaplugin._memory.executor.get_queued_task_count()
        df_dict = {"time": datetime.now().isoformat(), "active_users": active_users,
                   "vram_usage": round(100-np.sum(tot_free_vrams)/np.sum(tot_vrams)*100,1), "gpu_utilization": np.mean(gpu_utilizations),
                   "ram_usage": ram_percent, "cpu_load_avg_1m": cpu_load_avg_1m, "rel_proc_cpu_time": round(tot_cpu_time * 100 / p_time,1),
                   "total_messages_sent": total_messages_sent,  "total_processed_tokens": total_tokens, "current_active_tasks": current_active_tasks, "task_queue_count": task_queue_count,
                   "total_mb_transmitted": round(total_mb_transmitted,1), "net_err_total": err_total,
                   "total_disk_time": round(total_disk_time, 1), "total_disk_activity": round(total_mb_disk)}
        df = pd.DataFrame(data=[df_dict])
        file_path = os.path.join(settings.WORKING_DIRECTORY, "statistics", "main.csv")
        file_exists = os.path.exists(file_path)
        with open(file_path, 'a', newline='') as f:
            if not file_exists:
                df.to_csv(f, sep=';', index=False, header=True)
            else:
                df.to_csv(f, sep=';', index=False, header=False)

        # try:
        #     statistics_df = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/main.csv", sep=";")
        #     df = pd.concat([statistics_df, df])
        # except FileNotFoundError:
        #     pass
        # df.to_csv(settings.WORKING_DIRECTORY + "/statistics/main.csv", sep=";", index=False)



# def collect_user_info():
#     to_keep = {}
#     to_store = {}
#     with lock:
#         for key, value in VisitStatistics.distinct_session_keys.items():
#             if session_expired(value):
#                 to_store[key] = value
#             else:
#                 to_keep[key] = value
#         VisitStatistics.distinct_session_keys = to_keep
#
#     entries = []
#     for key, value in to_store.items():
#         is_mobile, browser_family, is_touch_capable = process_user_agent(value.user_agent)
#         entry = [calculate_session_time(value), value.accepted_languages.split(";")[0], value.is_user, is_mobile,
#                  browser_family, is_touch_capable, value.is_bot]
#         entries.append(entry)
#
#     names = ["visit_time", "accepted_languages", "is_user", "is_mobile", "browser_family", "touch_capable", "is_bot"]
#     df = pd.DataFrame(columns=names, data=entries)
#     statistics_names = [f"users_per_{max_between_time.seconds//60}_min", f"total_time_per_{max_between_time.seconds//60}_min",
#                         "time"]
#     df_statistics = pd.DataFrame(columns=statistics_names, data=[[len(entries), df["visit_time"].sum(), datetime.now()]])
#     try:
#         df2 = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/user_info.csv", sep=";")
#         df = pd.concat([df, df2])
#     except FileNotFoundError:
#         pass
#     try:
#         df2 = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/user_statistics.csv", sep=";")
#         df_statistics = pd.concat([df_statistics, df2])
#     except FileNotFoundError:
#         pass
#     df.to_csv(settings.WORKING_DIRECTORY + "/statistics/user_info.csv", sep=";", index=False)
#     df_statistics.to_csv(settings.WORKING_DIRECTORY + "/statistics/user_statistics.csv", sep=";", index=False)
#
#     p = psutil.Process(os.getpid())
#     core_num = p.cpu_num()
#     utilizations = psutil.cpu_percent(percpu=True)
#     core_utilization = utilizations[core_num]
#
#     names = ["time", "user_count", "avg_msg_count", "avg_time_spent", "total_msg_count", "total_time_spent", "core_utilization"]
#     msg_counts = []
#     time_spent = []
#     user_count = 0
#     with lock:
#         for key, value in SessionStatistics.distinct_user_sessions.items():
#             msg_counts.append(value["msg_count"])
#             time_spent.append(value["time_spent"])
#         user_count = len(SessionStatistics.distinct_user_sessions)
#         SessionStatistics.distinct_user_sessions = {}
#     df_sessions = pd.DataFrame(columns=names, data=[[datetime.now(), user_count,
#                                                      np.average(msg_counts) if len(msg_counts) != 0 else 0,
#                                                      np.average(time_spent) if len(time_spent) != 0 else 0,
#                                                       sum(msg_counts), sum(time_spent), core_utilization]])
#     try:
#         df2 = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/session_statistics.csv", sep=";")
#         df_sessions = pd.concat([df_sessions, df2])
#     except FileNotFoundError:
#         pass
#     df_sessions.to_csv(settings.WORKING_DIRECTORY + "/statistics/session_statistics.csv", sep=";", index=False)
#
#     time.sleep(max_between_time.seconds)
#     collect_user_info()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

KNOWN_BOTS = [
    "bot",
    "crawl",
    "spider",
    "slurp",
    "search",
    "bing",
    "yahoo",
    "duckduckgo",
    "baidu",
    "yandex",
    "sogou",
    "exabot",
    "facebot",
    "ia_archiver",
]

def is_bot(user_agent):
    user_agent = user_agent.lower()
    for bot in KNOWN_BOTS:
        if bot in user_agent:
            return True
    return False
#
class UserInfo:
    def __init__(self, request):
        self.first_visited = datetime.now()
        self.last_visited = datetime.now()
        self.ip_address = get_client_ip(request)
        self.accepted_languages = request.headers.get("Accept-Language", "")
        # self.is_user = request.user.is_authenticated
        self.is_user = True
        self.user_agent = request.headers.get("User-Agent", "")
        self.is_bot = is_bot(self.user_agent)

    def __str__(self):
        return f"Visit length: {self.last_visited - self.first_visited}\nIp: {self.ip_address}\n" \
               f"Languages: {self.accepted_languages}\nUser?: {self.is_user}\nUser agent: {self.user_agent}"
#
#
class VisitStatistics:
    distinct_session_keys = {}

    @staticmethod
    def register_request(request):
        key = request.session.session_key
        if key in VisitStatistics.distinct_session_keys:
            VisitStatistics.distinct_session_keys[key].last_visited = datetime.now()
        else:
            VisitStatistics.distinct_session_keys[key] = UserInfo(request)

class SessionStatistics:
    distinct_user_sessions = {}

    @staticmethod
    def register_infos(username, msg_count, time_spent):
        if not username in SessionStatistics.distinct_user_sessions:
            SessionStatistics.distinct_user_sessions[username] = {"msg_count": msg_count, "time_spent": time_spent}
        else:
            SessionStatistics.distinct_user_sessions[username]["msg_count"] += msg_count
            SessionStatistics.distinct_user_sessions[username]["time_spent"] += time_spent

class SimpleMiddleware:
    async_capable = True
    sync_capable = False
    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    async def __call__(self, request):
        # with lock:
        #     VisitStatistics.register_request(request)
        response = await self.get_response(request)
        return response