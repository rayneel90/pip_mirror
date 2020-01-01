"""
This module contains necessary functions for fetching the links as per the
preference mentioned in the config file
"""
import threading
import re
import queue
from builtins import super
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
import requests
from utils.helpers import *
import pandas as pd
from packaging.version import parse
import warnings
import os
from hashlib import sha256
from datetime import timedelta
import configparser
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
from time import time
# from tqdm import tqdm
# from urllib.request import urlretrieve


def get_pkglist(base: str, proxydict: dict, include: str, exclude: str) -> list:
    """
    Creates a list of the packages to download, from two strings containing
    the list of files to include and exclude respectively
    :param base: str. Base URL of the mirror from which files are to be
        downloaded
    :param proxydict: dict of format
        {'http':"link_of_http_proxy",
         'https': "link_of_https_proxy"
        }
    :param include: newline separated names in a string. list of packages to be
    downloaded
    :param exclude: newline separated names in a string. List of packages not
    to be downloaded
    :return:
    """
    html = bs(requests.get(base, proxies=proxydict, verify=False).text.lower(),
              'lxml')
    include_pkgs = include.lower().split()
    exclude_pkgs = exclude.lower().split()
    pkglist = [{'project': i.text, 'link': i['href']} for i in
               html.find_all('a') if i.text not in exclude_pkgs]
    if include_pkgs:
        pkglist = [i for i in pkglist if i['project'] in include_pkgs]
    return pkglist



class LinkFetcher(threading.Thread):
    def __init__(self, in_que, start, ptrn, proxies, location,
                 base_url="https://pypi.org/simple/"):
        super().__init__()
        self.in_queue = in_que
        self.starttime = start
        self.size = in_que.qsize()
        self.last = self.start
        self.base_url = base_url
        self.ptrn = ptrn
        self.proxydict = proxies
        self.locations = location

    def run(self):
        while True:
            pkg = self.in_queue.get()
            url = urljoin(self.base_url, pkg['link'])
            html = bs(
                requests.get(url, proxies=self.proxydict, verify=False).text,
                "lxml"
            )
            df = pd.DataFrame([
                {
                    "project": pkg['project'],
                    'link': itm['href'],
                    'filename': itm.text,
                    **parse_name(itm.text, self.ptrn)
                }
                for itm in html.find_all("a")
            ])
            dl_q = queue.Queue()
            for itm in filter_pkgs(df):
                dl_q.put(itm)
            dl_start = time()
            dl_location = os.path.join(
                self.locations['download'],
                pkg['project']
            )
            for i in range(3):
                f = FileDownloader(dl_q, dl_location, self.proxydict)
                f.setDaemon(True)
                f.start()
            dl_q.join()
            print("Finished Downloading: {} | Time took: {}".format(
                pkg['project'],
                timedelta(seconds=round(time()-dl_start))
            ), end="\r")
            # TODO: create index
            self.in_queue.task_done()


class FileDownloader(threading.Thread):
    def __init__(self, in_que, location, proxies):
        super().__init__()
        self.queue = in_que
        self.proxydict = proxies
        self.location = location

    def run(self) -> None:
        os.makedirs(self.location, exist_ok=True)
        while True:
            itm = self.queue.get()
            filname = os.path.join(self.location, itm['filename'])
            if os.path.exists(filname):
                with open(filname, 'rb') as fil:
                    binary = fil.read()
                if sha256(binary).hexdigest() != itm['link'][-64:]:
                    os.remove(filname)
                else:
                    self.queue.task_done()
                    continue
            try:
                binary = requests.get(itm['link'], proxies=self.proxydict,
                                      verify=False).content
            except requests.exceptions.ProxyError as e:
                continue # TODO: Create error log
            if sha256(binary).hexdigest() != itm['link'][-64:]:
                continue  # TODO: Create error log
            with open(filname, 'wb') as fil:
                fil.write(binary)
            self.queue.task_done()

def fetch_links(config):
    # config = configparser.ConfigParser()
    # config.read("pip_mirror.conf")
    base_url = config['GENERAL'].get("source", "https://pypi.org/simple")
    # link of mirror from where to download
    location = config['GENERAL']['mirror_path']
    locations = {
        "download": os.path.join(location, 'packages'),
        "index": os.path.join(location, 'simple')
    }  # path where to store packages
    proxydict = {
        "http": config['GENERAL'].get("http_proxy", ""),
        "https": config['GENERAL'].get("https_proxy", "")
    }  # proxy to be used for the calls

    pkg_q = queue.Queue()
    pkglist = get_pkglist(base_url, proxydict,
                          config.get("INCLUDE", "project", fallback=""),
                          config.get("EXCLUDE", "project", fallback=""))

    for pkg in pkglist:
        pkg_q.put(pkg)
    path_to_download = config['GENERAL']['mirror_path']
    n_worker = config['GENERAL'].getint("n_worker")
    ptrn = create_regex(config)
    start = time()
    for i in range(n_worker):
        t = LinkFetcher(pkg_q, start, ptrn, proxydict,
                           locations, base_url)
        t.setDaemon(True)
        t.start()
    pkg_q.join()
