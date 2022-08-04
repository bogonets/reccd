# -*- coding: utf-8 -*-

from inspect import iscoroutinefunction
from typing import Any, Dict, Iterable, List, Optional, Tuple

from reccd.module.errors import (
    ModuleCallbackCoroutineError,
    ModuleCallbackInvalidReturnValueError,
    ModuleCallbackNotFoundError,
    ModuleCallbackNotFoundRouteError,
    ModuleCallbackRouteRuntimeError,
    ModuleCallbackRuntimeError,
)
from reccd.module.mixin._module_base import ModuleBase
from reccd.route.dynamic_resource import DynamicResource
from reccd.variables.module import NAME_ON_ROUTES

RouteMethod = str
RoutePath = str
RouteCallable = Any
RouteTuple = Tuple[RouteMethod, RoutePath, Any]


class Route:
    def __init__(self, method: str, path: str, func):
        normalize_method = str(method).strip().upper()
        normalize_path = str(path).strip()

        self.method = normalize_method
        self.path = normalize_path
        self.func = func
        self.dynamic_resource = DynamicResource(normalize_path)

    def match(self, method: str, path: str) -> Optional[Dict[str, str]]:
        normalize_method = str(method).strip().upper()
        normalize_path = str(path).strip()

        if self.method != normalize_method:
            return None

        return self.dynamic_resource.match(normalize_path)


class ModuleRouter(ModuleBase):

    _routes: List[Route] = list()

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._routes = list()
        return instance

    @property
    def count_routes(self):
        return len(self._routes)

    @property
    def has_on_routes(self) -> bool:
        return self.has(NAME_ON_ROUTES)

    def _validate_routes_result_item(self, index: int, item: Any) -> None:
        if len(item) < 3:
            raise ModuleCallbackInvalidReturnValueError(
                self.module_name,
                NAME_ON_ROUTES,
                f"The length of element #{index} must be greater than or equal to 3",
            )

        assert len(item) >= 3

        method = item[0]
        if not isinstance(method, str):
            raise ModuleCallbackInvalidReturnValueError(
                self.module_name,
                NAME_ON_ROUTES,
                f"The 1st in element #{index} must be of type `str`",
            )

        path = item[1]
        if not isinstance(path, str):
            raise ModuleCallbackInvalidReturnValueError(
                self.module_name,
                NAME_ON_ROUTES,
                f"The 2nd in element #{index} must be of type `str`",
            )

        route = item[2]
        if not callable(route):
            raise ModuleCallbackInvalidReturnValueError(
                self.module_name,
                NAME_ON_ROUTES,
                f"The 3rd in element #{index} must be a callable",
            )

    def _validate_routes_result(self, result: Any) -> None:
        if result is None:
            raise ModuleCallbackInvalidReturnValueError(
                self.module_name,
                NAME_ON_ROUTES,
                "It must not be of `None`",
            )

        try:
            iterable_result = iter(result)
        except TypeError:
            raise ModuleCallbackInvalidReturnValueError(
                self.module_name,
                NAME_ON_ROUTES,
                "Not iterable",
            )

        for index, item in enumerate(iterable_result):
            self._validate_routes_result_item(index, item)

    def _on_routes(self) -> Iterable[RouteTuple]:
        callback = self.get(NAME_ON_ROUTES)
        if callback is None:
            raise ModuleCallbackNotFoundError(self.module_name, NAME_ON_ROUTES)

        if iscoroutinefunction(callback):
            raise ModuleCallbackCoroutineError(self.module_name, NAME_ON_ROUTES)

        try:
            result = callback()
        except BaseException as e:
            raise ModuleCallbackRuntimeError(self.module_name, NAME_ON_ROUTES) from e

        self._validate_routes_result(result)
        return result

    def update_routes(self) -> None:
        assert isinstance(self._routes, list)
        for method, path, route in self._on_routes():
            self._routes.append(Route(method, path, route))

    def get_route(self, method: str, path: str) -> Tuple[Any, Dict[str, str]]:
        assert isinstance(self._routes, list)
        for route in self._routes:
            match_info = route.match(method, path)
            if match_info is not None:
                return route.func, match_info
        raise ModuleCallbackNotFoundRouteError(
            self.module_name,
            NAME_ON_ROUTES,
            method,
            path,
        )

    async def route(self, method: str, path: str, *args, **kwargs) -> Any:
        callback, _ = self.get_route(method, path)
        assert callback is not None

        try:
            if iscoroutinefunction(callback):
                return await callback(*args, **kwargs)
            else:
                return callback(*args, **kwargs)

        except BaseException as e:
            raise ModuleCallbackRouteRuntimeError(
                self.module_name,
                NAME_ON_ROUTES,
                method,
                path,
            ) from e
