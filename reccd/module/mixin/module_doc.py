# -*- coding: utf-8 -*-

from reccd.module.errors import (
    ModuleAttributeInvalidValueError,
    ModuleAttributeNotFoundError,
)
from reccd.module.mixin._module_base import ModuleBase
from reccd.variables.plugin import NAME_DOC


class ModuleDoc(ModuleBase):
    @property
    def doc(self) -> str:
        if not self.has(NAME_DOC):
            raise ModuleAttributeNotFoundError(self.module_name, NAME_DOC)

        value = self.get(NAME_DOC)

        if value is None:
            raise ModuleAttributeInvalidValueError(
                self.module_name,
                NAME_DOC,
                "It must not be of `None`",
            )

        if not isinstance(value, str):
            raise ModuleAttributeInvalidValueError(
                self.module_name,
                NAME_DOC,
                "The attribute must be of type `str`",
            )

        return value
