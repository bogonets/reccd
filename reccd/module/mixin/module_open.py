# -*- coding: utf-8 -*-

from inspect import iscoroutinefunction

from reccd.module.errors import (
    ModuleCallbackInvalidStateError,
    ModuleCallbackNotCoroutineError,
    ModuleCallbackNotFoundError,
    ModuleCallbackRuntimeError,
)
from reccd.module.mixin._module_base import ModuleBase
from reccd.variables.module import NAME_ON_CLOSE, NAME_ON_OPEN


class ModuleOpen(ModuleBase):

    _opened: bool

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        instance._opened = False
        return instance

    @property
    def opened(self) -> bool:
        assert isinstance(self._opened, bool)
        return self._opened

    @property
    def has_on_open(self) -> bool:
        return self.has(NAME_ON_OPEN)

    @property
    def has_on_close(self) -> bool:
        return self.has(NAME_ON_CLOSE)

    async def on_open(self) -> None:
        if self._opened:
            raise ModuleCallbackInvalidStateError(
                self.module_name, NAME_ON_OPEN, "Already opened"
            )

        callback = self.get(NAME_ON_OPEN)
        if callback is None:
            raise ModuleCallbackNotFoundError(self.module_name, NAME_ON_OPEN)

        if not iscoroutinefunction(callback):
            raise ModuleCallbackNotCoroutineError(self.module_name, NAME_ON_OPEN)

        try:
            await callback()
        except BaseException as e:
            raise ModuleCallbackRuntimeError(self.module_name, NAME_ON_OPEN) from e
        else:
            self._opened = True

    async def on_close(self) -> None:
        if not self._opened:
            raise ModuleCallbackInvalidStateError(
                self.module_name, NAME_ON_CLOSE, "Not opened"
            )

        callback = self.get(NAME_ON_CLOSE)
        if callback is None:
            raise ModuleCallbackNotFoundError(self.module_name, NAME_ON_CLOSE)

        if not iscoroutinefunction(callback):
            raise ModuleCallbackNotCoroutineError(self.module_name, NAME_ON_CLOSE)

        try:
            await callback()
        except BaseException as e:
            raise ModuleCallbackRuntimeError(self.module_name, NAME_ON_CLOSE) from e
        else:
            self._opened = False
