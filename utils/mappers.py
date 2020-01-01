VERSION_MAPPER = {
    "3.7": ['py3', 'py37', 'cp37', 'py3.7'],
    '3.6': ['py3', 'py36', 'cp36', 'py3.6'],
    "3.5": ['py3', 'py35', 'cp35', 'py3.5'],
    "3.4": ['py3', 'py34', 'cp34', 'py3.4'],
    "3": ['py3', 'py37', 'cp37', 'py3.7', 'py36', 'cp36', 'py3.6',
            'py35', 'cp35', 'py3.5', 'py34', 'cp34', 'py3.4']
}

IMPLE_MAPPER = {
    'none': "none",
    "cpython-38": ['cp38', 'cp38m'],
    "cpython-37": ['cp37', 'cp37m'],
    "cpython-36": ['cp36', 'cp36m'],
    "cpython-35": ['cp35', 'cp35m'],
    "cpython-34": ['cp34', 'cp34m'],
    "all": ['none', 'cp38m', 'cp37m', 'cp36m', 'cp35m', 'cp34m', 'cp33m',
            'cp38', 'cp37', 'cp36', 'cp35', 'cp34', 'cp33']
}

PLATFORM_MAPPER = {
    "win32": ['win_amd64', 'win32'],
    "linux": ['manylinux1_x86_64', 'manylinux1_i686', 'manylinux2010_x86_64',
              'manylinux2010_i686', 'manylinux2014_x86_64', 'manylinux2014_i686'],
    "mac": []
}

TYPE_MAPPER = {
    "source": ['tar.gz', 'tar.bz'],
    "binary": ['whl'],
    "executable": ['exe', 'deb', 'rpm']
}

