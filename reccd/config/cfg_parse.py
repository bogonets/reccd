# -*- coding: utf-8 -*-

from configparser import ConfigParser
from typing import Dict

from reccd.variables.config import CFG_ENCODING, CFG_SECTION


def get_cfg_section(parser: ConfigParser, section=CFG_SECTION) -> Dict[str, str]:
    result = dict()
    for option in parser.options(section):
        result[option] = parser.get(section, option)
    return result


def get_cfg_section_by_text(cfg_text: str, section=CFG_SECTION) -> Dict[str, str]:
    parser = ConfigParser()
    parser.read_string(cfg_text)
    return get_cfg_section(parser, section)


def get_cfg_section_by_path(
    cfg_path: str,
    section=CFG_SECTION,
    encoding=CFG_ENCODING,
) -> Dict[str, str]:
    parser = ConfigParser()
    parser.read(cfg_path, encoding=encoding)
    return get_cfg_section(parser, section)
