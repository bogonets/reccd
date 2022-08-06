# -*- coding: utf-8 -*-

from reccd.variables.port import DEFAULT_SERVER_PORT

_1KB = 1024
_1MB = _1KB * 1024
_1GB = _1MB * 1024

MAX_SEND_MESSAGE_LENGTH = _1GB
MAX_RECEIVE_MESSAGE_LENGTH = _1GB

OPTIONS_KEY_TIMEOUT = "timeout"
OPTIONS_KEY_MAX_SEND_MESSAGE_LENGTH = "grpc.max_send_message_length"
OPTIONS_KEY_MAX_RECEIVE_MESSAGE_LENGTH = "grpc.max_receive_message_length"

DEFAULT_GRPC_OPTIONS = [
    (OPTIONS_KEY_MAX_SEND_MESSAGE_LENGTH, MAX_SEND_MESSAGE_LENGTH),
    (OPTIONS_KEY_MAX_RECEIVE_MESSAGE_LENGTH, MAX_RECEIVE_MESSAGE_LENGTH),
]

ACCEPTED_UDS_PORT_NUMBER = 1
"""The accepted UDS(Unix Domain Socket) port number is fixed as `1`.

Reference:
 - File: grpc/src/core/lib/iomgr/unix_sockets_posix.cc
 - Func: grpc_resolve_unix_domain_address
"""

DNS_URI_PREFIX = "dns:"
"""Prefix of DNS.
"""

UNIX_URI_PREFIX = "unix:"
"""Prefix of UDS(Unix Domain Socket).

Reference:
 - Site: `gRPC Name Resolution <https://grpc.github.io/grpc/cpp/md_doc_naming.html>`_
 - File: grpc/src/core/ext/transport/chttp2/server/chttp2_server.cc
"""

UNIX_ABSTRACT_URI_PREFIX = "unix-abstract:"
"""Prefix of UDS(Unix Domain Socket) in abstract namespace.

Reference:
 - Site: `gRPC Name Resolution <https://grpc.github.io/grpc/cpp/md_doc_naming.html>`_
 - File: grpc/src/core/ext/transport/chttp2/server/chttp2_server.cc
"""

DEFAULT_SERVER_BIND = "[::]"
DEFAULT_SERVER_ADDRESS = f"{DEFAULT_SERVER_BIND}:{DEFAULT_SERVER_PORT}"

REGISTER_KEY_RSA_SIZE = 2048

DEFAULT_HEARTBEAT_DELAY = 0.0
DEFAULT_HEARTBEAT_TIMEOUT = 5.0
DEFAULT_PACKET_MAX_SIZE = 100 * 1024 * 1024

DEFAULT_PICKLE_PROTOCOL_VERSION = 5
DEFAULT_PICKLE_ENCODING = "ASCII"

REGISTER_ANSWER_KEY_MIN_SM_SIZE = "min_sm_size"
REGISTER_ANSWER_KEY_MIN_SM_BYTE = "min_sm_byte"

M_GET = "GET"
M_HEAD = "HEAD"
M_POST = "POST"
M_PUT = "PUT"
M_DELETE = "DELETE"
M_CONNECT = "CONNECT"
M_OPTIONS = "OPTIONS"
M_TRACE = "TRACE"
M_PATCH = "PATCH"
