# -*- coding: utf-8 -*-

from multiprocessing.shared_memory import SharedMemory
from typing import Any, Dict, Iterable, List, Mapping, Optional

from numpy import ndarray
from type_serialize import ByteCoding
from type_serialize.byte.byte_coder import bytes_to_object

from reccd.packet.content_inspector import has_array, has_shared_memory
from reccd.packet.response import Response
from reccd.proto.daemon.daemon_api_pb2 import Content


class Unpacker:

    _coding: ByteCoding
    _encoding: str
    _args: List[Content]
    _kwargs: Dict[str, Content]
    _sms: Dict[str, SharedMemory]

    def __init__(
        self,
        coding: ByteCoding,
        encoding: str,
        args: Optional[Iterable[Content]] = None,
        kwargs: Optional[Mapping[str, Content]] = None,
        sms: Optional[Mapping[str, SharedMemory]] = None,
    ):
        self._coding = coding
        self._encoding = encoding
        self._args = list(args) if args else list()
        self._kwargs = dict(kwargs) if kwargs else dict()
        self._sms = dict(sms) if sms else dict()

    def content_to_any(self, content: Content) -> Any:
        if has_shared_memory(content):
            if not self._sms:
                raise ValueError("The shared-memory-list does not exist")
            if content.sm_name not in self._sms:
                raise IndexError(
                    f"The shared-memory('{content.sm_name}') does not exist"
                )
            size = content.size
            data = bytes(self._sms[content.sm_name].buf[:size])
        else:
            data = content.data

        if has_array(content):
            return ndarray(
                shape=content.array.shape,
                dtype=content.array.dtype,
                buffer=data,
                strides=content.array.strides,
            )
        else:
            return bytes_to_object(data=data, coding=self._coding)

    def args_to_anys(self) -> List[Any]:
        return [self.content_to_any(arg) for arg in self._args]

    def kwargs_to_anys(self) -> Dict[str, Any]:
        return {key: self.content_to_any(arg) for key, arg in self._kwargs.items()}

    def unpack(self) -> Response:
        args = self.args_to_anys()
        kwargs = self.kwargs_to_anys()
        return Response(*args, **kwargs)


def content_unpack(
    coding: ByteCoding,
    encoding: str,
    args: Optional[Iterable[Content]] = None,
    kwargs: Optional[Mapping[str, Content]] = None,
    sms: Optional[Mapping[str, SharedMemory]] = None,
) -> Response:
    unpacker = Unpacker(
        coding=coding,
        encoding=encoding,
        args=args,
        kwargs=kwargs,
        sms=sms,
    )
    return unpacker.unpack()
