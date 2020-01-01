import re
from utils.mappers import *
from packaging.version import parse
import pandas as pd


def create_regex(config) -> re.Pattern:
    """
    This takes the include and exclude section of the config file and creates
    the regex pattern. This pattern is subsequently used to filter out/in the
    packages to download.
    :param config:
    :return:
    """
    # create the extension map. the include_type always have precedence over
    # the exclude type.
    src_ptrn = re.compile(
    "^(?P<project>[0-9A-z_.-]*)"
    "-(?P<version>[0-9.a-z_]*)"
    "[.](?P<extn>tar.gz|tar.bz|zip)$")

    include_platform = config.get("INCLUDE", "platform", fallback="").split()
    exclude_platform = config.get("EXCLUDE", "platform", fallback="").split()
    if include_platform:
        platforms = "|".join([i for key, val in PLATFORM_MAPPER.items() for i
                              in val if key in include_platform])
    else:
        platforms = "|".join([i for key, val in PLATFORM_MAPPER.items() for i
                              in val if key in exclude_platform])

        include_platform = config.get("INCLUDE", "platform", fallback="").split()
        exclude_platform = config.get("EXCLUDE", "platform", fallback="").split()
        if include_platform:
            platforms = "|".join([i for key, val in PLATFORM_MAPPER.items() for i
                                  in val if key in include_platform])
        else:
            platforms = "|".join([i for key, val in PLATFORM_MAPPER.items() for i
                                  in val if key in exclude_platform])

    include_ver = config.get("INCLUDE", "py_ver", fallback="").split()
    exclude_ver = config.get("EXCLUDE", "py_ver", fallback="").split()
    if include_ver:
        ver = "|".join([i for key, val in VERSION_MAPPER.items() for i
                        in val if key in include_ver])
    else:
        ver = "|".join([i for key, val in VERSION_MAPPER.items() for i
                        in val if key in exclude_ver])

    include_imple = config.get("INCLUDE", "implementation", fallback="").split()
    exclude_imple = config.get("EXCLUDE", "impplementation", fallback="").split()
    if include_imple:
        imple = "|".join([i for key, val in IMPLE_MAPPER.items() for i
                          in val if key in include_imple])
    else:
        imple = "|".join([i for key, val in IMPLE_MAPPER.items() for i
                          in val if key in exclude_imple])
    bin_ptrn = re.compile(
        "^(?P<project>[0-9A-z_.]*)"
        "-(?P<version>[0-9.a-z_]*)"
        "-(?P<py_ver>{ver})"
        "-(?P<imple>{imple})"
        "-(?P<platform>{platform})"
        "[.](?P<extn>whl)$".format(
            ver=ver,
            imple=imple,
            platform=platforms,
        )
    )
    return {'source': src_ptrn, 'binary': bin_ptrn}


def parse_name(pkgname, ptrns):
    """
    Match pkgname against ptrns and return a dict or None

    :argument:
        pkgname: str contains the name to be parsed
        ptrns: dictionary with keys 'source' and 'binary' and corresponding
            compiled regex pattern as value

    :return:
        dict containing match groups or None if match is not found

    :example:
        import configparser
        config = configparser.ConfigParser()
        config.read("pip_mirror.conf")
        ptrns = create_regex(config)
        print(parse_name("numpy-1.18.0-cp37-cp37m-manylinux1_x86_64.whl",
            ptrns))
        >>> {'project': 'numpy', 'version': '1.18.0', 'py_ver': 'cp37',
             'imple': 'cp37m', 'platform': 'manylinux1_x86_64', 'extn': 'whl'}
        print(parse_name("python-Levenshtein-0.10.2.tar.gz", ptrns))
        >>> {'project': 'python-Levenshtein', 'version': '0.10.2',
             'extn': 'tar.gz'}
    """
    if pkgname.lower().endswith(".whl"):
        mtch = ptrns['binary'].match(pkgname)
    else:
        mtch = ptrns['source'].match(pkgname)
    return mtch.groupdict() if mtch else {}

def filter_pkgs(df: pd.DataFrame, keep_n: int = 3):
    """
    filter out older versions of packages

    :param df:
    :param keep_n:
    :return:
    """
    df = df[df.version.notnull()]
    df.version = df.version.apply(parse)
    df = df[~df.version.apply(
        lambda x: x.is_devrelease or x.is_prerelease or x.is_postrelease)]
    grouper = df.columns.intersection(
        ['py_ver', 'imple', 'platform', 'extn']).tolist()
    df = df.sort_values("version", ascending=False).groupby(
        grouper,
        as_index=False
    ).head(keep_n)
    return df.filter(['project', 'filename', 'link']).to_dict(orient='record')

