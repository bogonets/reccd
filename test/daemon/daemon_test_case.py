# -*- coding: utf-8 -*-

import os
from test.daemon import plugins
from unittest import IsolatedAsyncioTestCase

from reccd.package.package_utils import get_module_directory
from reccd.system.path_context import PathContext


class DaemonTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self._plugins_dir = get_module_directory(plugins)
        self._path_context = PathContext(self._plugins_dir, insert_operation=True)
        self._path_context.open()

        for plugin in self.test_module_names:
            self.assertTrue(os.path.isdir(os.path.join(self._plugins_dir, plugin)))

    def tearDown(self):
        self._path_context.close()

    @property
    def plugins_dir(self) -> str:
        return self._plugins_dir

    def _assert_plugin_name(self, name: str) -> str:
        self.assertTrue(name)
        plugin_dir = os.path.join(self._plugins_dir, name)
        self.assertTrue(os.path.isdir(plugin_dir))
        plugin_init_file = os.path.join(plugin_dir, "__init__.py")
        self.assertTrue(os.path.isfile(plugin_init_file))
        return name

    @property
    def reccd_test_performance(self):
        return self._assert_plugin_name("reccd_test_performance")

    @property
    def reccd_test_router(self):
        return self._assert_plugin_name("reccd_test_router")

    @property
    def test_module_names(self):
        return [
            self.reccd_test_performance,
            self.reccd_test_router,
        ]
