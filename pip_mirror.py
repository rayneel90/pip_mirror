"""
This is the top level script which is to be called to clone the pypi mirror.
it performs following tasks
    - take the arguments. It interprets / creates the .ini file
"""


import sys
from urllib import request
from utils import fetch_links
import argparse
import configparser
from time import sleep
import os
CLR_CMD = 'cls' if os.name=='nt' else 'clear'


def generate_config():
    print('Started creating default configuration file')
    config = configparser.ConfigParser()
    config['GENERAL'] = {
        "mirror_path": os.path.join(os.getcwd(), 'pip_mirror'),
        "source": 'https://pypi.org/simple',
        "n_worker": os.cpu_count()-1,
    }
    config['INCLUDE'] = {
        "type": "\nbinary\nsource",
        "platform": '\n'+sys.platform,
        "py_ver": '\n' + sys.version[:3],
        "implementation": "\n"+sys.implementation.cache_tag,
        "project": "\n"
    }
    config['EXCLUDE'] = {
        "type": "executable",
        "platform":"\nmac"
    }
    with open('pip_mirror.conf', 'w') as configfile:
        config.write(configfile)
    sleep(2)
    print("\nConfig file written successfully in {}".format(
        os.path.abspath('pip_mirror.conf')))


prsr = argparse.ArgumentParser(description="download/verify the mirror")
group = prsr.add_mutually_exclusive_group(required=True)
group.add_argument("-C", "--config",
                  help="path of the file. both relative and absolute path "
                       "works")
group.add_argument("--generate-config", action="store_const", const=True,
                   default=False)

# args = prsr.parse_args(["-C", r"E:\Office\SystemManagement\pip_mirror\trunk\pip_mirror.conf"])
os.system('cls')
args = prsr.parse_args()
if args.generate_config:
    generate_config()
    exit()

if os.path.exists(args.config):
    config = configparser.ConfigParser()
    config.read(args.config)
    if 'GENERAL' not in config:
        raise Exception('config file does not contain "General" section')
    a = fetch_links.fetch_links(config)
else:
    raise FileNotFoundError("Invalid file/path '{}'. Please run --generate-config to generate the configuration".format(args.config))
