# -*- coding: utf-8 -*-

import sys
from asyncio import run as asyncio_run
from asyncio import sleep
from typing import Final, List, Mapping, Optional

import grpc
from grpc.aio import ServicerContext
from type_serialize import ByteCoding
from type_serialize.variables import COMPRESS_LEVEL_BEST

from reccd.aio.connection import try_connection
from reccd.config.servicer_config import ServicerConfig
from reccd.daemon.daemon_client import heartbeat
from reccd.logging.logging import reccd_logger as logger
from reccd.memory.shared_memory_validator import validate_shared_memory
from reccd.module.module import Module
from reccd.packet.content_parameter import call_router
from reccd.proto.daemon.daemon_api_pb2 import (
    PacketA,
    PacketQ,
    Pat,
    Pit,
    RegisterA,
    RegisterCode,
    RegisterQ,
)
from reccd.proto.daemon.daemon_api_pb2_grpc import (
    DaemonApiServicer,
    add_DaemonApiServicer_to_server,
)
from reccd.uri.uds import is_uds_family
from reccd.variables.rpc import (
    ACCEPTED_UDS_PORT_NUMBER,
    DEFAULT_GRPC_OPTIONS,
    DEFAULT_HEARTBEAT_TIMEOUT,
    DEFAULT_PICKLE_ENCODING,
    DNS_URI_PREFIX,
    REGISTER_ANSWER_KEY_MIN_SM_BYTE,
    REGISTER_ANSWER_KEY_MIN_SM_SIZE,
)

DNS_URI_PREFIX_LEN: Final[int] = len(DNS_URI_PREFIX)


class DaemonServicer(DaemonApiServicer):
    def __init__(self, plugin: Module):
        self._plugin = plugin
        self._encoding = DEFAULT_PICKLE_ENCODING
        self._compress_level = COMPRESS_LEVEL_BEST

    def __repr__(self) -> str:
        return f"DaemonServicer<{self._plugin.module_name}>"

    def __str__(self) -> str:
        return f"DaemonServicer<{self._plugin.module_name}>"

    @property
    def plugin(self) -> Module:
        return self._plugin

    async def open(self) -> None:
        logger.info("Daemon opening ...")
        if self._plugin.has_on_open:
            await self._plugin.on_open()
        if self._plugin.has_on_routes:
            self._plugin.update_routes()
        logger.info("Daemon opened.")

    async def close(self) -> None:
        logger.info("Daemon closing ...")
        if self._plugin.has_on_close:
            await self._plugin.on_close()
        logger.info("Daemon closed.")

    async def Heartbeat(self, request: Pit, context: ServicerContext) -> Pat:
        logger.debug(f"Heartbeat(delay={request.delay})")
        await sleep(delay=request.delay)
        return Pat(ok=True)

    async def Register(self, request: RegisterQ, context: ServicerContext) -> RegisterA:
        session = request.session
        args = list(request.args)
        kwargs = dict(request.kwargs)
        logger.debug(f"Register(session={session},args={args},kwargs={kwargs})")

        if self._plugin.has_on_register:
            result = await self._plugin.on_register(*args, **kwargs)
            code = RegisterCode.Success
        else:
            result = None
            code = RegisterCode.NotFoundRegisterFunction

        test_sm_name = request.test_sm_name
        test_sm_pass = request.test_sm_pass
        if test_sm_name and test_sm_pass:
            is_sm = validate_shared_memory(request.test_sm_name, request.test_sm_pass)
        else:
            is_sm = False

        if is_sm and result is not None:
            if isinstance(result, Mapping):
                min_sm_size = result.get(REGISTER_ANSWER_KEY_MIN_SM_SIZE, 0)
                min_sm_byte = result.get(REGISTER_ANSWER_KEY_MIN_SM_BYTE, 0)
            else:
                min_sm_size = getattr(result, REGISTER_ANSWER_KEY_MIN_SM_SIZE, 0)
                min_sm_byte = getattr(result, REGISTER_ANSWER_KEY_MIN_SM_BYTE, 0)
        else:
            min_sm_size = 0
            min_sm_byte = 0

        return RegisterA(
            code=code,
            is_sm=is_sm,
            min_sm_size=min_sm_size,
            min_sm_byte=min_sm_byte,
        )

    async def Packet(self, request: PacketQ, context: ServicerContext) -> PacketA:
        session = request.session
        method = request.method
        path = request.path
        logger.debug(f"Packet(session={session},method={method},path={path})")
        route, match_info = self._plugin.get_route(method, path)
        result = await call_router(
            func=route,
            match_info=match_info,
            coding=ByteCoding(request.coding),
            encoding=self._encoding,
            compress_level=self._compress_level,
            args=request.args,
            kwargs=request.kwargs,
            sm_names=request.sm_names,
        )
        return PacketA(args=result.args, kwargs=result.kwargs)


class _AcceptInfo(object):

    __slots__ = ("servicer", "server", "accepted_port_number")

    def __init__(
        self,
        servicer: DaemonServicer,
        server: grpc.aio.Server,
        accepted_port_number: Optional[int] = None,
    ):
        self.servicer = servicer
        self.server = server
        self.accepted_port_number = accepted_port_number


def create_daemon_server(
    address: str,
    module_name: str,
    packages_dirs: Optional[List[str]] = None,
) -> _AcceptInfo:
    if packages_dirs:
        for packages_dir in packages_dirs:
            sys.path.insert(0, packages_dir)
            logger.debug(f"Insert packages directory: {packages_dir}")

    if address.startswith(DNS_URI_PREFIX):
        logger.debug(f"Strip unnecessary prefix: '{DNS_URI_PREFIX}'")
        address = address[DNS_URI_PREFIX_LEN:]

    logger.info(f"Module name: {module_name}")
    logger.info(f"Servicer address: {address}")
    logger.info(f"Arguments: {sys.argv}")

    plugin = Module(module_name)
    servicer = DaemonServicer(plugin)

    server = grpc.aio.server(options=DEFAULT_GRPC_OPTIONS)
    accepted_port_number = server.add_insecure_port(address)

    add_DaemonApiServicer_to_server(servicer, server)

    if is_uds_family(address):
        assert accepted_port_number == ACCEPTED_UDS_PORT_NUMBER
        logger.info("Socket type: Unix Domain Socket")
        return _AcceptInfo(servicer, server)
    else:
        assert accepted_port_number != ACCEPTED_UDS_PORT_NUMBER
        logger.info("Socket type: IP Address")
        logger.info(f"Accepted port number: {accepted_port_number}")
        return _AcceptInfo(servicer, server, accepted_port_number)


async def wait_connectable(
    address: str,
    retry_delay: Optional[float] = None,
    max_attempts: Optional[int] = None,
    heartbeat_timeout: Optional[float] = DEFAULT_HEARTBEAT_TIMEOUT,
) -> bool:
    def _try_cb(i: int, m: int) -> None:
        assert 0 <= i <= m
        attempts_msg = f"{i+1}/{m}"
        logger.debug(f"wait_connectable() -> Try connection ({attempts_msg}) ...")

    def _retry_cb(i: int, m: int) -> None:
        assert 0 <= i <= m
        attempts_msg = f"{i+1}/{m}"
        logger.debug(f"wait_connectable() -> Retry connection ({attempts_msg}) ...")

    def _success_cb(i: int, m: int) -> None:
        assert 0 <= i <= m
        logger.info("wait_connectable() -> Self connection successful !!")

    def _failure_cb(i: int, m: int) -> None:
        assert 0 <= i <= m
        logger.debug("wait_connectable() -> Self connection failure.")

    logger.info(f"Try connection address: {address}")
    return await try_connection(
        predictor=lambda: heartbeat(address, delay=0, timeout=heartbeat_timeout),
        retry_delay=retry_delay,
        max_attempts=max_attempts,
        try_cb=_try_cb,
        retry_cb=_retry_cb,
        success_cb=_success_cb,
        failure_cb=_failure_cb,
    )


async def run_daemon_server(config: ServicerConfig, wait_connect=True) -> None:
    if not config.module:
        raise ValueError("The module name is required")

    logger.info(f"Start the daemon server: {config.module}")

    accept_info = create_daemon_server(config.address, config.module)
    servicer = accept_info.servicer
    await servicer.open()
    server = accept_info.server
    accepted_port_number = accept_info.accepted_port_number

    await server.start()

    if wait_connect:
        if accepted_port_number is None:
            await wait_connectable(config.address)
        else:
            await wait_connectable(f"localhost:{accepted_port_number}")

    try:
        logger.info("SERVER IS RUNNING !!")
        await server.wait_for_termination()
    finally:
        # Shuts down the server with 0 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(0)
        await servicer.close()
        logger.info(f"Daemon server done: {config.module}")


def run_daemon_until_complete(config: ServicerConfig) -> int:
    try:
        asyncio_run(run_daemon_server(config))
        logger.info("Daemon completed successfully")
        return 0
    except KeyboardInterrupt:
        logger.warning("Received an interrupt")
        return 0
    except BaseException as e:
        logger.exception(e)
        return 1
