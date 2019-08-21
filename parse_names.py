from sqlalchemy import create_engine
import pandas as pd
import re

engine = create_engine('mysql://root:pass@123@127.0.0.1:3306/pip')


df = pd.read_sql_table('links', engine)
print(df.shape)
print(df[df.name.str.lower().str.contains("\.tar")].shape)
print(df[df.name.str.lower().str.contains("\.zip")].shape)

whl_ptrn = re.compile("(?P<name>[a-z0-9-. _]+?)"
                      "(-(?P<version>[0-9.a-z-_+()-]+?))"
                      "(-(?P<py_ver>(p|c)[a-z0-9.,+]+?))"
                      "(-(?P<imple>[a-z0-9_]+?))"
                      "(-(?P<platform>[a-z0-9_.-]+)?)"
                      "\.(?P<extn>whl)")

tar_ptrn = re.compile("(?P<name>[a-z0-9-. _]+?)"
                      "(-+(?P<version>[0-9.a-z]+?)-*){0,1}"
                      "(\.(?P<platform>(linux|mac).+)){0,1}"
                      "\.(?P<extn>tar.gz|tar.bz2)")

lst=[]

for idx, row in df.iterrows():
    # idx, row = next(df.iterrows())
    # if ".exe" in row['name'] or ".msi" in row['name']:
    #     continue
    # if ".whl" in row['name']:
    try:
        tmp = tar_ptrn.match(row['name'].lower()).groupdict()
        tmp['pkg'] = row['name']
        tmp['link'] = row['link']
        lst.append(tmp)
    except:
        print(row['name'])
        break

dat = pd.DataFrame(lst)
dat.to_sql('index_tar', engine, index=False, if_exists='replace')