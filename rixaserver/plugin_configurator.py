import click
import subprocess
import os
import sys
import shutil
import rixaserver


def query_yes_no(question, default="no"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")



@click.group()
def plug_conf():
    pass

@plug_conf.command(help="Analyzes all supplied directories for JS files and adds them to the available API functions")
@click.option('--recursive', is_flag=True)
def run_js_transpiler(recursive):
    raise Exception("Unfinished. Use notebook.")

@plug_conf.command(help="Generate a plugin from a supplied python file using its documentation")
def autogenerate_plugin():
    raise Exception("Not finished. Use notebook")

@plug_conf.command(help="Check wether RIXA works and info required for determining problems")
def debug():
    try:
        import rixaserver
        rixaserver.sanity_check(verbose=True)
        import plugins
        farnsworth = """⠀⠀⠀⠀⣀⣀⣠⣤⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢀⣴⠟⠛⠉⠉⠉⠉⠛⠛⠷⣦⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢰⡿⠁⠀⠀⣾⡆⠀⠀⠀⠀⠀⠀⠈⠛⠛⢷⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠸⣿⠀⠀⠀⠀⠀⠀⠰⠾⠿⠂⠀⠀⠀⠀⠀⠉⠙⠻⢷⣶⣤⣀⡀⠀⠀⠀⠀⠀
⠀⢹⣧⠀⠀⠛⠀⠀⠀⢀⣶⠿⠛⠃⠀⣀⣠⣤⣤⣀⣠⣴⣾⠟⠛⢷⡄⠀⠀⠀
⠀⠀⠻⣧⠀⠀⠀⠀⠀⠀⠀⢀⣴⣾⣿⡿⠋⠀⠉⢻⣿⣿⣟⠀⠀⠈⣿⠀⠀⠀
⠀⠀⠀⠹⣷⡀⠀⠀⣀⣠⣤⣼⣿⣿⣿⣇⠀⠀⠀⢠⣿⠉⠛⠛⠷⣶⡟⠀⠀⠀
⠀⠀⠀⠀⠘⣿⣶⣿⣋⠉⠁⠈⢿⣿⣿⣿⣶⣤⣴⠿⠃⢰⣿⠃⠀⠙⣿⡀⠀⠀
⠀⠀⠀⠀⠀⣿⠁⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⡄⠀⠙⠛⢿⣶⣿⡇⠀⠀
⠀⠀⠀⠀⠀⠙⢷⣄⠀⢻⣆⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠀⠀⠙⠿⣦⣤⡀
⠀⠀⠀⠀⠀⠀⠀⠹⣧⣀⣡⡀⠀⠀⠀⠀⠀⠀⣼⡏⠀⣴⠿⢛⣻⡿⠛⠛⠋⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠉⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⣰⡟⠋⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⡾⠏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉
Good news everyone. RIXA works!"""
        print(farnsworth)
    except Exception as e:
        print(e)
        print("Local RIXA does not work")




@plug_conf.command(help="Create files to make the current (or supplied) directory a RIXA working directory.")
@click.argument('path', required=False)
def initialize_dir(path):
    if not path:
        path = os.getcwd()
    if not os.path.isdir(path):
        raise Exception(f"'{path}' is not a valid directory path!")
    if len(os.listdir(path)) != 0:
        should_continue = query_yes_no("The directory you want to use as a working dir is not empty. Continue anyway?")
        if not should_continue:
            print("Exiting...")
            return

    try:
        import plugins as pl
        import shutil
        example_path = os.path.join(pl.__path__[0], "example_wd")
        for i in os.listdir(example_path):
            copy_path = os.path.join(example_path, i)
            if os.path.isdir(copy_path):
                os.mkdir(os.path.join(path, i))
            else:
                shutil.copy2(copy_path, path)
        print(f"New working directoy has been set up in {path}.")

    except Exception as e:
        print(e)


@plug_conf.command(help="Dump all available public settings into a file. Format may be incorrect.")
@click.argument("path")
def dump_settings(path):
    rixaserver._change_to_local()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RIXAWebserver.settings')
    from django.conf import settings
    with open(path, "w") as file:
        for i in settings.ALL_SETTINGS:
            file.write(f"{i}={settings.ALL_SETTINGS[i]}\n")


@plug_conf.command(help="Build, update or modify the database of the current RIXA instance")
@click.option('--rebuild', is_flag=True)
def update_db(rebuild):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RIXAWebserver.settings')
    from django.conf import settings
    assert settings.WORKING_DIRECTORY
    result = subprocess.run("rixaserver django migrate", capture_output=True, text=True, shell=True, check=False)
    if result.returncode !=0:
        print(result.stdout)
        raise Exception("DB building failed!")
    else:
        print("Successfully built DB")

# @plug_conf.command()
# def open_config_location():
#     path = ""
#     try:
#         if "win" in sys.platform:
#             os.startfile(path)
#         if os.name == "posix":
#             opener = "open" if sys.platform == "darwin" else "xdg-open"
#             subprocess.call([opener, path])
#     except:
#         print(f"Can't open file browser. The location is: {path}")
