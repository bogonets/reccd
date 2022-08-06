# -*- coding: utf-8 -*-

from asyncio import TimeoutError, wait_for
from typing import Any, Final, List, Optional, Tuple
from uuid import uuid4

import grpc
from grpc.aio._channel import Channel  # noqa
from type_serialize import ByteCoding
from type_serialize.variables import COMPRESS_LEVEL_BEST

from reccd.chrono.datetime import tznow
from reccd.daemon.daemon_answer import DaemonAnswer
from reccd.logging.logging import reccd_logger as logger
from reccd.memory.shared_memory_queue import SharedMemoryQueue
from reccd.memory.shared_memory_validator import (
    SharedMemoryTestInfo,
    register_shared_memory,
)
from reccd.packet.content_packer import ContentPacker
from reccd.packet.content_unpacker import content_unpack
from reccd.proto.daemon.daemon_api_pb2 import (
    PacketA,
    PacketQ,
    Pat,
    Pit,
    RegisterA,
    RegisterCode,
    RegisterQ,
)
from reccd.proto.daemon.daemon_api_pb2_grpc import DaemonApiStub
from reccd.variables.rpc import (
    DEFAULT_GRPC_OPTIONS,
    DEFAULT_HEARTBEAT_TIMEOUT,
    DEFAULT_PICKLE_ENCODING,
    M_CONNECT,
    M_DELETE,
    M_GET,
    M_HEAD,
    M_OPTIONS,
    M_PATCH,
    M_POST,
    M_PUT,
    M_TRACE,
    MAX_RECEIVE_MESSAGE_LENGTH,
    MAX_SEND_MESSAGE_LENGTH,
    OPTIONS_KEY_MAX_RECEIVE_MESSAGE_LENGTH,
    OPTIONS_KEY_MAX_SEND_MESSAGE_LENGTH,
    OPTIONS_KEY_TIMEOUT,
)


async def heartbeat(
    address: str,
    delay: float = 0,
    timeout: Optional[float] = DEFAULT_HEARTBEAT_TIMEOUT,
) -> bool:
    async with grpc.aio.insecure_channel(
        address, options=DEFAULT_GRPC_OPTIONS
    ) as channel:
        # grpc.channel_ready_future(channel)
        stub = DaemonApiStub(channel)
        options = dict()
        if timeout is not None:
            options["timeout"] = timeout
        response = await stub.Heartbeat(Pit(delay=delay), **options)
    return response.ok


class DaemonClient:

    REGISTER_SUCCESS: Final[int] = int(RegisterCode.Success)
    REGISTER_NOT_FOUND: Final[int] = int(RegisterCode.NotFoundRegisterFunction)

    _session: str
    _channel: Optional[Channel] = None
    _stub: Optional[DaemonApiStub] = None
    _is_sm: Optional[bool] = None

    def __init__(
        self,
        address: str,
        timeout: Optional[float] = None,
        disable_shared_memory=False,
        max_send_message_length=MAX_SEND_MESSAGE_LENGTH,
        max_receive_message_length=MAX_RECEIVE_MESSAGE_LENGTH,
        verbose=0,
    ):
        self._session = uuid4().hex
        self._address = address
        self._options = dict()
        if timeout is not None:
            self._options[OPTIONS_KEY_TIMEOUT] = timeout
        self._smq = SharedMemoryQueue()
        self._encoding = DEFAULT_PICKLE_ENCODING
        self._compress_level = COMPRESS_LEVEL_BEST
        self._coding = ByteCoding.MsgpackZlib
        self._min_sm_size = 0
        self._min_sm_byte = 0
        self._max_send_message_length = max_send_message_length
        self._max_receive_message_length = max_receive_message_length

        self.disable_shared_memory = disable_shared_memory
        self.verbose = verbose

    def __repr__(self) -> str:
        return f"DaemonClient<{self._address}>"

    def __str__(self) -> str:
        return f"DaemonClient<{self._address}>"

    @property
    def address(self) -> str:
        return self._address

    @property
    def possible_shared_memory(self) -> bool:
        return bool(self._is_sm)

    @property
    def timeout(self) -> Optional[float]:
        return self._options.get(OPTIONS_KEY_TIMEOUT)

    @timeout.setter
    def timeout(self, value: float) -> None:
        self._options[OPTIONS_KEY_TIMEOUT] = value

    @property
    def channel_options(self) -> List[Tuple[str, Any]]:
        return [
            (OPTIONS_KEY_MAX_SEND_MESSAGE_LENGTH, self._max_send_message_length),
            (OPTIONS_KEY_MAX_RECEIVE_MESSAGE_LENGTH, self._max_receive_message_length),
        ]

    def is_open(self) -> bool:
        return self._channel is not None

    async def _close(self) -> None:
        assert self._channel is not None
        assert self._stub is not None
        await self._channel.close()
        self._channel = None
        self._stub = None
        self._smq.clear()

    async def open(self) -> None:
        self._channel = grpc.aio.insecure_channel(
            self._address,
            options=self.channel_options,
        )

        self._stub = DaemonApiStub(self._channel)

        try:
            await wait_for(self._channel.channel_ready(), timeout=self.timeout)
        except TimeoutError:
            await self._close()
            raise

    async def close(self) -> None:
        await self._close()

    async def heartbeat(self, delay: float = 0) -> bool:
        assert self._stub is not None
        response = await self._stub.Heartbeat(Pit(delay=delay), **self._options)
        assert isinstance(response, Pat)
        return response.ok

    async def register(self, *args: str, **kwargs: str) -> int:
        assert self._stub is not None

        with register_shared_memory(self.disable_shared_memory) as test:
            assert isinstance(test, SharedMemoryTestInfo)
            request = RegisterQ(
                session=self._session,
                args=args,
                kwargs=kwargs,
                test_sm_name=test.name,
                test_sm_pass=test.data,
            )
            response = await self._stub.Register(request, **self._options)

        assert isinstance(response, RegisterA)
        self._is_sm = response.is_sm

        if response.min_sm_size > self._min_sm_size:
            self._min_sm_size = response.min_sm_size
        if response.min_sm_byte > self._min_sm_byte:
            self._min_sm_byte = response.min_sm_byte

        if response.code == self.REGISTER_SUCCESS:
            pass
        elif response.code == self.REGISTER_NOT_FOUND:
            logger.warning("Not found register function")
        else:
            logger.error(f"Unknown register code: {response.code}")
        return response.code

    async def request(self, method: str, path: str, *args, **kwargs) -> DaemonAnswer:
        assert self._stub is not None

        coding = self._coding
        encoding = self._encoding
        compress_level = self._compress_level

        use_sm = self.possible_shared_memory and not self.disable_shared_memory
        smq: Optional[SharedMemoryQueue]
        if use_sm:
            min_sm_size = self._min_sm_size
            min_sm_byte = self._min_sm_byte
            smq = self._smq
        else:
            min_sm_size = 0
            min_sm_byte = 0
            smq = None

        renter = self._smq.multi_rent(min_sm_size, min_sm_byte)
        with renter as sms:
            packer = ContentPacker(
                coding=coding,
                compress_level=compress_level,
                args=args,
                kwargs=kwargs,
                smq=smq,
            )

            packer_begin = tznow()
            with packer as contents:
                if self.verbose >= 1:
                    packer_seconds = (tznow() - packer_begin).total_seconds()
                    packer_elapsed = round(packer_seconds, 3)
                    logger.debug(f"Packer[sm={use_sm}]: {packer_elapsed}s")

                packet = PacketQ(
                    session=self._session,
                    method=method if method else str(),
                    path=path if path else str(),
                    coding=int(coding.value),  # type: ignore[arg-type]
                    args=contents.args,
                    kwargs=contents.kwargs,
                    sm_names=sms.keys(),
                )

                handshake_begin = tznow()
                response = await self._stub.Packet(packet, **self._options)
                if self.verbose >= 1:
                    handshake_seconds = (tznow() - handshake_begin).total_seconds()
                    handshake_elapsed = round(handshake_seconds, 3)
                    logger.debug(f"Handshake[sm={use_sm}]: {handshake_elapsed}s")

            assert isinstance(response, PacketA)
            unpacker_begin = tznow()
            result = content_unpack(
                coding=coding,
                encoding=encoding,
                args=response.args,
                kwargs=response.kwargs,
                sms=sms,
            )
            if self.verbose >= 1:
                unpacker_seconds = (tznow() - unpacker_begin).total_seconds()
                unpacker_elapsed = round(unpacker_seconds, 3)
                logger.debug(f"Unpacker[sm={use_sm}]: {unpacker_elapsed}s")

            return result

    async def get(self, path: str, *args, **kwargs):
        return await self.request(M_GET, path, *args, **kwargs)

    async def head(self, path: str, *args, **kwargs):
        return await self.request(M_HEAD, path, *args, **kwargs)

    async def post(self, path: str, *args, **kwargs):
        return await self.request(M_POST, path, *args, **kwargs)

    async def put(self, path: str, *args, **kwargs):
        return await self.request(M_PUT, path, *args, **kwargs)

    async def delete(self, path: str, *args, **kwargs):
        return await self.request(M_DELETE, path, *args, **kwargs)

    async def connect(self, path: str, *args, **kwargs):
        return await self.request(M_CONNECT, path, *args, **kwargs)

    async def options(self, path: str, *args, **kwargs):
        return await self.request(M_OPTIONS, path, *args, **kwargs)

    async def trace(self, path: str, *args, **kwargs):
        return await self.request(M_TRACE, path, *args, **kwargs)

    async def patch(self, path: str, *args, **kwargs):
        return await self.request(M_PATCH, path, *args, **kwargs)
