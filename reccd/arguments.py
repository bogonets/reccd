# -*- coding: utf-8 -*-

from argparse import REMAINDER, ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional

from reccd.logging.logging import SEVERITIES, SEVERITY_NAME_INFO
from reccd.variables.module import MODULE_NAME_PREFIX
from reccd.variables.rpc import DEFAULT_SERVER_ADDRESS

CMD_CLIENT: Final[str] = "client"
CMD_MODULES: Final[str] = "modules"
CMD_SERVER: Final[str] = "server"

SKIP_MODULE: Final[str] = "-"

PROG: Final[str] = "reccd"
DESCRIPTION: Final[str] = "Daemon helper for the ANSWER"
EPILOG: Final[str] = ""

SERVER_HELP: Final[str] = "Start the gRPC daemon server"
SERVER_EPILOG = f"""
Use '{SKIP_MODULE}' to skip module names in command line arguments.
"""

CLIENT_HELP: Final[str] = "It communicates with the daemon server"
CLIENT_EPILOG: Final[str] = ""

MODULES_HELP: Final[str] = "Prints a list of available modules"

KV_SEPARATOR: Final[str] = "="

DEFAULT_MODULE_PREFIX: Final[str] = MODULE_NAME_PREFIX
DEFAULT_SEVERITY: Final[str] = SEVERITY_NAME_INFO
DEFAULT_METHOD: Final[str] = "GET"
DEFAULT_PATH: Final[str] = "/"
DEFAULT_HEARTBEAT_DELAY: Final[float] = 0.0
DEFAULT_TIMEOUT: Final[float] = 30.0


@lru_cache
def version() -> str:
    # [IMPORTANT] Avoid 'circular import' issues
    from reccd import __version__

    return __version__


def get_default_server_namespace() -> Namespace:
    return Namespace(
        address=DEFAULT_SERVER_ADDRESS,
    )


def add_server_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_SERVER,
        help=SERVER_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=SERVER_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)

    default_namespace = get_default_server_namespace()
    default_address = default_namespace.address
    assert default_address

    parser.add_argument(
        "--config",
        "-c",
        default=None,
        metavar="file",
        help="Configuration file path",
    )
    parser.add_argument(
        "--address",
        "-a",
        default=None,
        metavar="addr",
        help=f"gRPC bind address (default: '{default_address}')",
    )
    parser.add_argument(
        "module",
        default=None,
        nargs="?",
        help="Plugin module name",
    )
    parser.add_argument(
        "opts",
        nargs=REMAINDER,
        help="Arguments of plugins",
    )


def add_client_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_CLIENT,
        help=CLIENT_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=CLIENT_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)

    parser.add_argument(
        "--heartbeat",
        "-H",
        action="store_true",
        default=False,
        help="It only sends a 'HEARTBEAT' signal and exits",
    )
    parser.add_argument(
        "--skip-heartbeat",
        action="store_true",
        default=False,
        help="It does not send a 'HEARTBEAT' signal when creating a client",
    )

    parser.add_argument(
        "--register",
        "-R",
        action="store_true",
        default=False,
        help="It only sends a 'REGISTER' signal and exits",
    )
    parser.add_argument(
        "--skip-register",
        action="store_true",
        default=False,
        help="It does not send a 'REGISTER' signal when creating a client",
    )

    parser.add_argument(
        "--timeout",
        "-t",
        default=DEFAULT_TIMEOUT,
        type=float,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--disable-shared-memory",
        action="store_true",
        default=False,
        help="Suppress shared memory usage",
    )

    parser.add_argument(
        "--address",
        "-a",
        metavar="addr",
        default=DEFAULT_SERVER_ADDRESS,
        help=f"gRPC host address (default: '{DEFAULT_SERVER_ADDRESS}')",
    )
    parser.add_argument(
        "--method",
        "-m",
        "-M",
        "-x",
        "-X",
        default=DEFAULT_METHOD,
        help=f"Request method (default: '{DEFAULT_METHOD}')",
    )
    parser.add_argument(
        "--path",
        "-p",
        "-P",
        default=DEFAULT_PATH,
        help=f"Request path (default: '{DEFAULT_PATH}')",
    )
    parser.add_argument(
        "--keyword",
        "-k",
        metavar=f"k{KV_SEPARATOR}v",
        action="append",
        help=f"Keyword argument in the form 'key{KV_SEPARATOR}value' for request",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Be more verbose/talkative during the operation",
    )

    parser.add_argument(
        "args",
        nargs=REMAINDER,
        help="Positional arguments for request",
    )


def add_modules_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(name=CMD_MODULES, help=MODULES_HELP)
    assert isinstance(parser, ArgumentParser)


def default_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--module-prefix",
        metavar="prefix",
        default=DEFAULT_MODULE_PREFIX,
        help=f"The prefix of the module (default: '{DEFAULT_MODULE_PREFIX}')",
    )
    parser.add_argument(
        "--default-logging",
        "-l",
        action="store_true",
        default=False,
        help="Use default logging",
    )
    parser.add_argument(
        "--simple-logging",
        "-s",
        action="store_true",
        default=False,
        help="Use simple logging",
    )
    parser.add_argument(
        "--severity",
        choices=SEVERITIES,
        default=DEFAULT_SEVERITY,
        help=f"Logging severity (default: '{DEFAULT_SEVERITY}')",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable debugging mode and change logging severity to 'DEBUG'",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Be more verbose/talkative during the operation",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=version(),
    )

    subparsers = parser.add_subparsers(dest="cmd")
    add_server_parser(subparsers)
    add_client_parser(subparsers)
    add_modules_parser(subparsers)
    return parser


def get_default_arguments(
    cmdline: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = default_argument_parser()
    return parser.parse_known_args(cmdline, namespace)[0]
