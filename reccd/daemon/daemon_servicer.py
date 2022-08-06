# -*- coding: utf-8 -*-

import sys
from asyncio import run as asyncio_run
from asyncio import sleep
from pathlib import Path
from typing import Final, List, Mapping, Optional

from type_serialize import ByteCoding
from type_serialize.variables import COMPRESS_LEVEL_BEST

from reccd.aio.connection import try_connection
from reccd.daemon.daemon_client import insecure_heartbeat, secure_heartbeat
from reccd.logging.logging import reccd_logger as logger
from reccd.memory.shared_memory_validator import validate_shared_memory
from reccd.module.module import Module
from reccd.packet.parameter_matcher import call_router
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
from reccd.rpc.server import (
    Server,
    ServerCredentials,
    ServicerContext,
    create_grpc_aio_server,
    ssl_server_credentials,
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
        server: Server,
        accepted_port_number: Optional[int] = None,
    ):
        self.servicer = servicer
        self.server = server
        self.accepted_port_number = accepted_port_number


def create_server_credentials(
    private_key_path: str,
    certificate_chain_path: str,
) -> ServerCredentials:
    private_key = Path(private_key_path).read_bytes()
    certificate_chain = Path(certificate_chain_path).read_bytes()

    # A list of pairs of the form
    # [PEM-encoded private key, PEM-encoded certificate chain]
    private_key_certificate_chain_pairs = [(private_key, certificate_chain)]

    return ssl_server_credentials(private_key_certificate_chain_pairs)


def create_daemon_server(
    bind_address: str,
    module_name: str,
    private_key_path: Optional[str] = None,
    certificate_chain_path: Optional[str] = None,
    packages_dirs: Optional[List[str]] = None,
) -> _AcceptInfo:
    if packages_dirs:
        for packages_dir in packages_dirs:
            sys.path.insert(0, packages_dir)
            logger.debug(f"Insert packages directory: {packages_dir}")

    if bind_address.startswith(DNS_URI_PREFIX):
        logger.debug(f"Strip unnecessary prefix: '{DNS_URI_PREFIX}'")
        bind_address = bind_address[DNS_URI_PREFIX_LEN:]

    logger.info(f"Module name: {module_name}")
    logger.info(f"Servicer address: {bind_address}")
    logger.info(f"Arguments: {sys.argv}")

    plugin = Module(module_name)
    servicer = DaemonServicer(plugin)

    server = create_grpc_aio_server(options=DEFAULT_GRPC_OPTIONS)

    if private_key_path and certificate_chain_path:
        server_credentials = create_server_credentials(
            private_key_path,
            certificate_chain_path,
        )
        logger.info("Create server credentials")
        logger.info(f"Private key path: {private_key_path}")
        logger.info(f"Certificate chain path: {certificate_chain_path}")
        accepted_port_number = server.add_secure_port(bind_address, server_credentials)
    else:
        accepted_port_number = server.add_insecure_port(bind_address)

    add_DaemonApiServicer_to_server(servicer, server)

    if is_uds_family(bind_address):
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
    certificate_chain_path: Optional[str] = None,
    retry_delay: Optional[float] = None,
    max_attempts: Optional[int] = None,
    heartbeat_timeout: Optional[float] = DEFAULT_HEARTBEAT_TIMEOUT,
) -> bool:
    def _predictor():
        if certificate_chain_path:
            return secure_heartbeat(
                address=address,
                root_certificates_path=certificate_chain_path,
                delay=0,
                timeout=heartbeat_timeout,
            )
        else:
            return insecure_heartbeat(
                address=address,
                delay=0,
                timeout=heartbeat_timeout,
            )

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
        predictor=_predictor,
        retry_delay=retry_delay,
        max_attempts=max_attempts,
        try_cb=_try_cb,
        retry_cb=_retry_cb,
        success_cb=_success_cb,
        failure_cb=_failure_cb,
    )


async def run_daemon_server(
    bind_address: str,
    module_name: str,
    private_key_path: Optional[str] = None,
    certificate_chain_path: Optional[str] = None,
    wait_connect=True,
) -> None:
    if not module_name:
        raise ValueError("The module name is required")

    logger.info(f"Start the daemon server: {module_name}")

    accept_info = create_daemon_server(
        bind_address=bind_address,
        module_name=module_name,
        private_key_path=private_key_path,
        certificate_chain_path=certificate_chain_path,
        packages_dirs=None,
    )
    servicer = accept_info.servicer
    await servicer.open()
    server = accept_info.server
    accepted_port_number = accept_info.accepted_port_number

    await server.start()

    if wait_connect:
        if accepted_port_number is None:
            test_address = bind_address
        else:
            test_address = f"localhost:{accepted_port_number}"
        await wait_connectable(test_address, certificate_chain_path)

    try:
        logger.info("SERVER IS RUNNING !!")
        await server.wait_for_termination()
    finally:
        # Shuts down the server with 0 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(0)
        await servicer.close()
        logger.info(f"Daemon server done: {module_name}")


def run_daemon_until_complete(
    bind_address: str,
    module_name: str,
    private_key_path: Optional[str] = None,
    certificate_chain_path: Optional[str] = None,
    wait_connect=True,
) -> int:
    try:
        asyncio_run(
            run_daemon_server(
                bind_address=bind_address,
                module_name=module_name,
                private_key_path=private_key_path,
                certificate_chain_path=certificate_chain_path,
                wait_connect=wait_connect,
            )
        )
        logger.info("Daemon completed successfully")
        return 0
    except KeyboardInterrupt:
        logger.warning("Received an interrupt")
        return 0
    except BaseException as e:
        logger.exception(e)
        return 1
