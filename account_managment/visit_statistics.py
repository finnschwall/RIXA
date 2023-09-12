import threading
from datetime import datetime, timedelta
import time
import pandas as pd
from user_agents import parse

lock = threading.Lock()

max_between_time = timedelta(minutes=30)


def collect_user_info():
    to_keep = {}
    to_store = {}
    lock.acquire()
    for key, value in PageStatistics.distinct_session_keys.items():
        if value.session_expired():
            to_store[key] = value
        else:
            to_keep[key] = value
    PageStatistics.distinct_session_keys = to_keep
    lock.release()

    entries = []
    for key, value in to_store.items():
        user_agent = parse(value.user_agent)
        entry = [(value.last_visited - value.first_visited).seconds, value.accepted_languages.split(";")[0],
                 value.is_user,
                 user_agent.is_mobile, user_agent.browser.family, user_agent.is_touch_capable]
        entries.append(entry)
    names = ["visit_time", "accepted_languages", "is_user", "is_mobile", "browser_family", "touch_capable"]
    df = pd.DataFrame(columns=names, data=entries)
    try:
        df2 = pd.read_csv("user_statistics.csv", sep=";")
        df = pd.concat([df, df2])
    except:
        pass
    df.to_csv("user_statistics.csv", sep=";", index=False)

    time.sleep(max_between_time.seconds)
    collect_user_info()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class UserInfo:
    def __init__(self, request):
        self.first_visited = datetime.now()
        self.last_visited = datetime.now()
        self.ip_address = get_client_ip(request)
        self.accepted_languages = request.headers["Accept-Language"]
        self.is_user = request.user.is_authenticated
        self.user_agent = request.headers["User-Agent"]

    def __str__(self):
        return f"Visit length: {self.last_visited - self.first_visited}\nIp: {self.ip_address}\n" \
               f"Languages: {self.accepted_languages}\nUser?: {self.is_user}\nUser agent: {self.user_agent}"

    def session_expired(self):
        if datetime.now() > self.last_visited + max_between_time:
            return True
        else:
            return False


class PageStatistics:
    distinct_session_keys = {}

    @staticmethod
    def register_request(request):
        key = request.session.session_key
        if key in PageStatistics.distinct_session_keys:
            PageStatistics.distinct_session_keys[key].last_visited = datetime.now()
            if not PageStatistics.distinct_session_keys[key].is_user and request.user.is_authenticated:
                PageStatistics.distinct_session_keys[key].is_user = True
        else:
            PageStatistics.distinct_session_keys[key] = UserInfo(request)
        # print(f"Collected {''.join([str(i) for i in to_store.values()])}")


class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lock.acquire()
        PageStatistics.register_request(request)
        lock.release()
        response = self.get_response(request)
        return response

# t = threading.Thread(name='collect_user_info', target=collect_user_info)
# t.daemon = True
# t.start()
