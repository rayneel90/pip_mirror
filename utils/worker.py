import threading
from urllib.parse import urljoin
import queue
from time import time
import os
from hashlib import sha256
from datetime import timedelta
from bs4 import BeautifulSoup as bs
import requests
from urllib import request
from utils.helpers import *


class LinkFetcher(threading.Thread):
    ptrn = {
        'binary': re.compile(
            r'(?P<project>[0-9A-z_.]*)-'
            r'(?P<version>[0-9.a-z_-]*)'
            r'-(?P<py_ver>[0-9a-z.]*)'
            r'-(?P<imple>[0-9a-z]*)'
            r'-(?P<platform>[0-9a-z-_.]*)'
            r'(?P<extn>.whl)'
        ),
        'source': re.compile(
            r'^(?P<project>[0-9A-z_ .-]*)-'
            r'(?P<version>[:0-9.a-z_-]*)'
            r'(?P<extn>.tar.gz|.zip)$'
        )
    }
    def __init__(self, in_que, err_q, start, filters,location,
                 base_url="https://pypi.org/simple/"):
        super().__init__()
        self.in_queue = in_que
        self.starttime = start
        self.size = in_que.qsize()
        self.last = self.start
        self.base_url = base_url
        self.location = location
        self.err_q = err_q
        self.filters = filters

    def run(self):
        while True:
            pkg = self.in_queue.get()
            if pkg['project'] == 'ipython_genutils':
                pkg['project'] = 'ipython-genutils'
            url = urljoin(self.base_url, pkg['link'])
            html = bs(
                request.urlopen(url).read(),
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
            if 'version' not in df.columns:
                self.err_q.put(pkg['project'])
                build_index(self.location, pkg['project'])
                continue
            dl_q = queue.Queue()
            for itm in filter_pkgs(df, self.filters):
                dl_q.put(itm)
            if not dl_q.qsize():
                self.err_q.put(pkg['project'])
                build_index(self.location, pkg['project'])
                continue
            dl_start = time()
            dl_location = self.location / 'packages' / pkg['project']

            for i in range(3):
                f = FileDownloader(dl_q, dl_location)
                f.setDaemon(True)
                f.start()
            dl_q.join()
            print("Finished Downloading: {} | Time took: {}\n\n".format(
                pkg['project'],
                timedelta(seconds=round(time()-dl_start))
            ))
            build_index(self.location, pkg['project'])
            self.in_queue.task_done()


class FileDownloader(threading.Thread):
    def __init__(self, in_que, location):
        super().__init__()
        self.queue = in_que
        self.location = location

    def run(self) -> None:
        self.location.mkdir(parents=True, exist_ok=True)
        while True:
            itm = self.queue.get()
            filname = self.location / itm['filename']  # type: Path
            if filname.exists():
                binary = filname.read_bytes()
                if sha256(binary).hexdigest() == itm['link'][-64:]:
                    self.queue.task_done()
                    continue
            # try:
            request.urlretrieve(itm['link'], filname)
            print(filname.name)
            # except:
            #     print("error occurred")
            #     pass  # TODO: handle exception
            self.queue.task_done()
