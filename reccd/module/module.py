# -*- coding: utf-8 -*-

from typing import List

from reccd.module.mixin.module_doc import ModuleDoc
from reccd.module.mixin.module_open import ModuleOpen
from reccd.module.mixin.module_register import ModuleRegister
from reccd.module.mixin.module_router import ModuleRouter
from reccd.module.mixin.module_version import ModuleVersion
from reccd.package.package_utils import filter_module_names
from reccd.variables.module import MODULE_NAME_PREFIX


class Module(
    ModuleDoc,
    ModuleOpen,
    ModuleRegister,
    ModuleRouter,
    ModuleVersion,
):
    def __init__(self, module_name: str, isolate=False):
        self._module = self.import_module(module_name, isolate=isolate)


def find_and_strip_module_prefix(prefix=MODULE_NAME_PREFIX) -> List[str]:
    modules = filter_module_names(prefix)
    module_name_begin = len(prefix)
    return list(map(lambda x: x[module_name_begin:].strip(), modules))
