"""
This module contains necessary functions for fetching the links as per the
preference mentioned in the config file
"""
import queue
from bs4 import BeautifulSoup as bs
from pathlib import Path
# from time import time
from utils.worker import  LinkFetcher
# from urllib import request
from utils.helpers import *

def get_pkglist(base: str, include: str, exclude: str) -> list:
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
    html = bs(request.urlopen(base).read().lower(), 'lxml')
    include_pkgs = set(include.lower().split())
    exclude_pkgs = set(exclude.lower().split())
    pkglist = [{'project': i.text, 'link': i['href']} for i in
               html.find_all('a') if i.text not in exclude_pkgs]
    if include_pkgs:
        pkglist = [i for i in pkglist if i['project'] in include_pkgs]
    return pkglist


def fetch_links(config):
    #   Set Proxy
    proxy = request.ProxyHandler(request.getproxies())
    opener = request.build_opener(proxy)
    request.install_opener(opener)

    base_url = config['GENERAL'].get("source", "https://pypi.org/simple")
    # link of mirror from where to download
    location = Path(config['GENERAL']['mirror_path'])  # path where to store packages

    pkg_q = queue.Queue()
    err_q = queue.Queue()
    print("Fetching Package-list")
    pkglist = get_pkglist(base_url,
                          config.get("INCLUDE", "project", fallback=""),
                          config.get("EXCLUDE", "project", fallback=""))
    print("Package-list fetched successfully. Following packages will be "
          "mirrored:")
    print(", ".join([i['project'] for i in pkglist]))
    for pkg in pkglist:
        pkg_q.put(pkg)
    n_worker = config['GENERAL'].getint("n_worker")
    filters = create_filters(config)
    start = time()
    for i in range(n_worker//3):
        t = LinkFetcher(pkg_q, err_q, start, filters, location, base_url)
        t.setDaemon(True)
        t.start()
    pkg_q.join()
    build_simple(location)
    errlist = []
    while 1:
        try:
            errlist.append(err_q.get_nowait())
        except:
            break
    with open('errorlist.txt', 'w') as fil:
        fil.write('\n'.join(errlist))


# import configparser
# from pathlib import Path
# from utils.helpers import build_index
# config = configparser.ConfigParser()
# config.read("pip_mirror.conf")
# location = Path(config['GENERAL']['mirror_path'])
# build_index(location, 'cudf')
# fetch_links(config)