# Do the servercrash challenge. Change any of these variables and then load a plugin. Change is_remote to make your
# memory cooler (and add leaks)
# personal note: maybe add some safeguards
import enum

class LoadType(enum.Enum):
    UNSAFE = 0
    MAIN_SERVER = 10
    SERVER_MANAGED_PLUGIN = 20
    STANDALONE_CODE = 30

loadtype = LoadType.UNSAFE

plugin_system_active = False
parse_mode = True
cur_conf = None
is_remote = False
is_server = True

p_id = -1
call_architecture = ""
thread_locals = None

all_available_functions = {}
available_nlp_backends = []
show_all_exceptions = True
async_loop = None
api_init_funcs = []


serverless = True

standalone_mode = True
jupyter_mode = True
