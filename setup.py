# -*- coding: utf-8 -*-

import os
from setuptools import setup
from typing import List

SOURCE_PATH = os.path.abspath(__file__)
SOURCE_DIR = os.path.dirname(SOURCE_PATH)
REQUIREMENTS_MAIN = os.path.join(SOURCE_DIR, "requirements.main.txt")


def install_requires(encoding="utf-8") -> List[str]:
    with open(REQUIREMENTS_MAIN, encoding=encoding) as f:
        content = f.read()
    lines = content.split("\n")
    lines = map(lambda x: x.strip(), lines)
    lines = filter(lambda x: x and x[0] != "#", lines)
    return list(lines)


if __name__ == "__main__":
    setup(install_requires=install_requires())
