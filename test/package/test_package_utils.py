# -*- coding: utf-8 -*-

import os
from importlib import import_module
from unittest import TestCase, main

from reccd.package.package_utils import get_module_directory


class PackageUtilsTestCase(TestCase):
    def test_get_recc_module_directory(self):
        recc_module_directory = get_module_directory(import_module("recc"))
        self.assertTrue(os.path.isdir(recc_module_directory))


if __name__ == "__main__":
    main()
