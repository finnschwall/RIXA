import os
import sys
import subprocess
import platform
import warnings
def _change_to_local():
    parent_dir = os.path.dirname(__path__[0])
    sys.path.insert(0, parent_dir)
    # os.chdir(parent_dir)

def sanity_check(verbose=False):
    python_version = platform.python_version_tuple()


    if verbose:
        print(f"System interpreter: {sys.base_prefix == sys.prefix}")
        print(f"Python version: {python_version}")
        print(f"Architecture: {platform.machine()}")
        cur_platform = platform.system()
        print(f"Platform: {cur_platform}")
        print(f"Full platform: {platform.platform()}")


        try:
            result = subprocess.run(["which" if cur_platform=="Linux" else "where", 'python'], capture_output=True, text=True, check=False)
            str = '?????' if result.returncode != 0 else result.stdout.split('\n')[0]
        except Exception as e:
            str = e
        print(f"Sys python: {str}")

        try:
            config_dir = os.environ["RIXA_WD"]
            print(f"WD: {config_dir}")
            print(f"WD is env: True")
        except KeyError:
            current_directory = os.getcwd()
            files = os.listdir(current_directory)
            if "config.ini" in files:
                print(f"WD: {current_directory}")
                print(f"WD is env: False")
            else:
                print("WD: None")



        try:
            result = subprocess.run(["pyenv", 'root'], capture_output=True, text=True, check=False)
            str = 'No pyenv' if result.returncode != 0 else result.stdout.split('\n')[0]
        except:
            str = "No pyenv"
        print(f"Pyenv: {str}")
        try:
            result = subprocess.run(["conda", 'version'], capture_output=True, text=True, check=True)
            str = 'No Conda' if result.returncode != 0 else result.stdout.split('\n')[0]
        except:
            str = "No Conda"
        print(f"Conda: {str}")
        try:
            subprocess.check_output("make --version".split()).decode('ascii')
            print("Make: OK")
        except:
            print("Make: FAILED")
        try:
            subprocess.check_output("g++ --version".split()).decode('ascii')
            print("g++: OK")
        except:
            print("g++: FAILED")


        try:
            import math
            import psutil
            print("here")
            # r1 = subprocess.run("nvidia-smi --query-gpu=memory.total --format=csv".split(), capture_output=True, text=True, check=True)
            r1 = subprocess.check_output("nvidia-smi --query-gpu=memory.free --format=csv".split()).decode('ascii').split('\n')[:-1][1]

            r2 = subprocess.check_output("nvidia-smi --query-gpu=memory.total --format=csv".split()).decode(
                'ascii').split('\n')[:-1][1]
            r3 = subprocess.check_output("nvidia-smi --query-gpu=count --format=csv".split()).decode(
                'ascii').split('\n')[:-1][1]
            r4 = subprocess.check_output("nvidia-smi --query-gpu=name --format=csv".split()).decode(
                'ascii').split('\n')[:-1][1]

            print(f"Number av GPUs: {r3}")
            print(f"Primary: {r4}")
            print(f"VRAM: {int(r1[:-3])}/{r2}")
            tot = round(psutil.virtual_memory()[1]/1024**2 + int(r1[:-3]))

        except Exception as e:
            # print(e)
            print("No supported GPU found!")
            tot = round(psutil.virtual_memory()[1] / 1024 ** 2)
        total_cpu_mem = math.floor(psutil.virtual_memory().total / (1024 * 1024))
        print(f"RAM: {psutil.virtual_memory()[1] / 1024 ** 2:.0f}/{total_cpu_mem} MiB")
        print(f"Tot Av: ~{tot/1024:.2f} GiB")
        print(f"Can run 7B LLM?:  {'Probably' if tot > 7000  else 'Probably not'}")
        print(f"Can run 13B LLM?: {'Probably' if tot > 12000 else 'Probably not'}")
        print(f"Can run 30B LLM?: {'Probably' if tot > 20000 else 'Probably not'}")

        import numpy as np
        import time


        matrix_size = 5000
        matrix_a = np.random.rand(matrix_size, matrix_size)
        matrix_b = np.random.rand(matrix_size, matrix_size)
        start_time = time.time()
        result_matrix=np.dot(matrix_a, matrix_b)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Rough CPU comp ability: {matrix_size ** 3 / (elapsed_time * 1e9):.2f} GFLOPS")

    if python_version[0] != '3':
        warnings.warn("Python 2 is not supported!")
    if int(python_version[1]) < 10:
        warnings.warn("Python version lower than recommended (> 3.11.X).")
    if int(python_version[1]) < 4:
        warnings.warn("Python versions < 3.4 will not work!")




def launch():
    _change_to_local()
    if "--dev" not in sys.argv and "runserver" in sys.argv and "REDIRECT_OUTPUT_DJANGO" not in os.environ:
        res = subprocess.run("rixaserver --dev django showmigrations | grep '\[ \]'", shell=True, text=True,
                             capture_output=True)
        if res.stdout:
            raise Exception("The database you are using is faulty!"
                                         "\nLikely you will need to do 'rixaserver update-db'")
    try:
        sys.argv.remove("--dev")
    except:
        pass
    if len(sys.argv) > 1 and (sys.argv[1]=="django" or "REDIRECT_OUTPUT_DJANGO" in os.environ or sys.argv[1]=="runserver"):
        os.environ["REDIRECT_OUTPUT_DJANGO"] = "True"
        if sys.argv[1]=="django":
            sys.argv.pop(1)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RIXAWebserver.settings')
        try:
            from django.core.management import execute_from_command_line
        except ImportError as exc:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc
        # print(sys.argv)
        execute_from_command_line(sys.argv)
    else:
        from .plugin_configurator import plug_conf
        plug_conf(sys.argv[1:])


