import requests
import json
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
import pandas as pd
from tqdm import tqdm

engine = create_engine('mysql://root:pass@123@127.0.0.1:3306/pip')
dat = requests.get("https://hugovk.github.io/top-pypi-packages/top-pypi-packages-365-days.json").text
dat = pd.DataFrame(json.loads(dat)['rows'])
pkgs = dat.project

for pkg in tqdm(pkgs):
# pkg = next(iter(pkgs))
    txt = requests.get('https://pypi.org/simple/'+pkg).text
    souped = BeautifulSoup(txt, 'lxml')
    links = souped.findAll('a')
    df = pd.DataFrame([{'name': i.text, 'link': i['href']} for i in links])
    df.to_sql('links', engine, index=False, if_exists='append')

