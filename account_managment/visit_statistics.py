import threading
from datetime import datetime, timedelta
import time
import pandas as pd
from django.conf import settings
from user_agents import parse
import re
from asgiref.sync import iscoroutinefunction, markcoroutinefunction
lock = threading.Lock()
max_between_time = timedelta(minutes=settings.STATISTICS_COLLECTION_INTERVAL, seconds=0)


def calculate_session_time(value):
    return (value.last_visited - value.first_visited).seconds//60


def process_user_agent(user_agent_str):
    user_agent = parse(user_agent_str)
    return user_agent.is_mobile, user_agent.browser.family, user_agent.is_touch_capable


def session_expired(user_info):
    return datetime.now() > user_info.last_visited + max_between_time


def collect_user_info():
    to_keep = {}
    to_store = {}
    with lock:
        for key, value in PageStatistics.distinct_session_keys.items():
            if session_expired(value):
                to_store[key] = value
            else:
                to_keep[key] = value
        PageStatistics.distinct_session_keys = to_keep

    entries = []
    for key, value in to_store.items():
        is_mobile, browser_family, is_touch_capable = process_user_agent(value.user_agent)
        entry = [calculate_session_time(value), value.accepted_languages.split(";")[0], value.is_user, is_mobile,
                 browser_family, is_touch_capable, value.is_bot]
        entries.append(entry)

    names = ["visit_time", "accepted_languages", "is_user", "is_mobile", "browser_family", "touch_capable", "is_bot"]
    df = pd.DataFrame(columns=names, data=entries)
    statistics_names = [f"users_per_{max_between_time.seconds//60}_min", f"total_time_per_{max_between_time.seconds//60}_min",
                        "time"]
    df_statistics = pd.DataFrame(columns=statistics_names, data=[[len(entries), df["visit_time"].sum(), datetime.now()]])
    try:
        df2 = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/user_info.csv", sep=";")
        df = pd.concat([df, df2])
    except FileNotFoundError:
        pass
    try:
        df2 = pd.read_csv(settings.WORKING_DIRECTORY + "/statistics/user_statistics.csv", sep=";")
        df_statistics = pd.concat([df_statistics, df2])
    except FileNotFoundError:
        pass
    df.to_csv(settings.WORKING_DIRECTORY + "/statistics/user_info.csv", sep=";", index=False)
    df_statistics.to_csv(settings.WORKING_DIRECTORY + "/statistics/user_statistics.csv", sep=";", index=False)
    time.sleep(max_between_time.seconds)
    collect_user_info()


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
class PageStatistics:
    distinct_session_keys = {}

    @staticmethod
    def register_request(request):
        key = request.session.session_key
        if key in PageStatistics.distinct_session_keys:
            PageStatistics.distinct_session_keys[key].last_visited = datetime.now()
            # if request.user.is_authenticated:
            #     PageStatistics.distinct_session_keys[key].is_user = True
        else:
            PageStatistics.distinct_session_keys[key] = UserInfo(request)
#
#

class SimpleMiddleware:
    async_capable = True
    sync_capable = False
    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    async def __call__(self, request):
        with lock:
            PageStatistics.register_request(request)
        response = await self.get_response(request)
        return response




# lock = threading.Lock()
#
# max_between_time = timedelta(minutes=30)


# def collect_user_info():
#     to_keep = {}
#     to_store = {}
#     lock.acquire()
#     for key, value in PageStatistics.distinct_session_keys.items():
#         if value.session_expired():
#             to_store[key] = value
#         else:
#             to_keep[key] = value
#     PageStatistics.distinct_session_keys = to_keep
#     lock.release()
#
#     entries = []
#     for key, value in to_store.items():
#         user_agent = parse(value.user_agent)
#         entry = [(value.last_visited - value.first_visited).seconds, value.accepted_languages.split(";")[0],
#                  value.is_user,
#                  user_agent.is_mobile, user_agent.browser.family, user_agent.is_touch_capable]
#         entries.append(entry)
#     names = ["visit_time", "accepted_languages", "is_user", "is_mobile", "browser_family", "touch_capable"]
#     df = pd.DataFrame(columns=names, data=entries)
#     try:
#         df2 = pd.read_csv("user_statistics.csv", sep=";")
#         df = pd.concat([df, df2])
#     except:
#         pass
#     df.to_csv("user_statistics.csv", sep=";", index=False)
#
#     time.sleep(max_between_time.seconds)
#     collect_user_info()
#
#
# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip
#
#
# class UserInfo:
#     def __init__(self, request):
#         self.first_visited = datetime.now()
#         self.last_visited = datetime.now()
#         self.ip_address = get_client_ip(request)
#         self.accepted_languages = request.headers["Accept-Language"]
#         self.is_user = request.user.is_authenticated
#         self.user_agent = request.headers["User-Agent"]
#
#     def __str__(self):
#         return f"Visit length: {self.last_visited - self.first_visited}\nIp: {self.ip_address}\n" \
#                f"Languages: {self.accepted_languages}\nUser?: {self.is_user}\nUser agent: {self.user_agent}"
#
#     def session_expired(self):
#         if datetime.now() > self.last_visited + max_between_time:
#             return True
#         else:
#             return False
#
#
# class PageStatistics:
#     distinct_session_keys = {}
#
#     @staticmethod
#     def register_request(request):
#         key = request.session.session_key
#         if key in PageStatistics.distinct_session_keys:
#             PageStatistics.distinct_session_keys[key].last_visited = datetime.now()
#             if not PageStatistics.distinct_session_keys[key].is_user and request.user.is_authenticated:
#                 PageStatistics.distinct_session_keys[key].is_user = True
#         else:
#             PageStatistics.distinct_session_keys[key] = UserInfo(request)
#
#
# class SimpleMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         lock.acquire()
#         PageStatistics.register_request(request)
#         lock.release()
#         response = self.get_response(request)
#         return response

# t = threading.Thread(name='collect_user_info', target=collect_user_info)
# t.daemon = True
# t.start()
