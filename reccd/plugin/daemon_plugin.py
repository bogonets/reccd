# -*- coding: utf-8 -*-

from reccd.plugin.mixin.plugin_open import PluginOpen
from reccd.plugin.mixin.plugin_register import PluginRegister
from reccd.plugin.mixin.plugin_router import PluginRouter


class DaemonPlugin(
    PluginOpen,
    PluginRegister,
    PluginRouter,
):
    def __init__(self, module_name: str):
        self._module = self.import_module(module_name)
        self._routes = list()
