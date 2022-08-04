# -*- coding: utf-8 -*-

from reccd.module.mixin.module_doc import ModuleDoc
from reccd.module.mixin.module_open import ModuleOpen
from reccd.module.mixin.module_register import ModuleRegister
from reccd.module.mixin.module_router import ModuleRouter
from reccd.module.mixin.module_version import ModuleVersion


class Module(
    ModuleDoc,
    ModuleOpen,
    ModuleRegister,
    ModuleRouter,
    ModuleVersion,
):
    def __init__(self, module_name: str, isolate=False):
        self._module = self.import_module(module_name, isolate=isolate)
