# -*- coding: utf-8 -*-

from inspect import iscoroutinefunction

from reccd.module.errors import (
    ModuleCallbackInvalidReturnValueError,
    ModuleCallbackInvalidStateError,
    ModuleCallbackNotCoroutineError,
    ModuleCallbackNotFoundError,
    ModuleCallbackRuntimeError,
)
from reccd.module.mixin._module_base import ModuleBase
from reccd.variables.module import NAME_ON_REGISTER


class ModuleRegister(ModuleBase):

    _registered = False

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        instance._registered = False
        return instance

    @property
    def registered(self) -> bool:
        assert isinstance(self._registered, bool)
        return self._registered

    @property
    def has_on_register(self) -> bool:
        return self.has(NAME_ON_REGISTER)

    async def on_register(self, *args, **kwargs) -> int:
        if self._registered:
            raise ModuleCallbackInvalidStateError(
                self.module_name, NAME_ON_REGISTER, "Already registered"
            )

        callback = self.get(NAME_ON_REGISTER)
        if callback is None:
            raise ModuleCallbackNotFoundError(self.module_name, NAME_ON_REGISTER)

        if not iscoroutinefunction(callback):
            raise ModuleCallbackNotCoroutineError(self.module_name, NAME_ON_REGISTER)

        try:
            result = await callback(*args, **kwargs)
        except BaseException as e:
            raise ModuleCallbackRuntimeError(self.module_name, NAME_ON_REGISTER) from e

        if not isinstance(result, int):
            raise ModuleCallbackInvalidReturnValueError(
                self.module_name,
                NAME_ON_REGISTER,
                "It must be of type `int`",
            )

        self._registered = True
        return result
