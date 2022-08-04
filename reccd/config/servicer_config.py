# -*- coding: utf-8 -*-

from argparse import REMAINDER, ArgumentParser, Namespace, RawDescriptionHelpFormatter
from typing import List, Optional, Tuple

from reccd.argparse.namespace_utils import right_join
from reccd.argparse.typing_namespace import typing_namespace
from reccd.config.cfg_parse import get_cfg_section_by_path
from reccd.config.env_parse import get_envs, get_file_envs
from reccd.variables.config import (
    SERVICER_DESCRIPTION,
    SERVICER_EPILOG,
    SERVICER_PROG,
    SKIP_MODULE,
)
from reccd.variables.rpc import DEFAULT_DAEMON_ADDRESS


class ServicerConfig(Namespace):
    address: str
    verbose: int

    module: Optional[str]
    opts: Optional[List[str]]


class ExtraFlags:
    show_modules: bool


def parse_servicer_arguments(
    args: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = ArgumentParser(
        prog=SERVICER_PROG,
        description=SERVICER_DESCRIPTION,
        epilog=SERVICER_EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        default=False,
        help="List of modules",
    )
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
        metavar="addr",
        default=DEFAULT_DAEMON_ADDRESS,
        help=f"gRPC bind address (default: '{DEFAULT_DAEMON_ADDRESS}')",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Be more verbose/talkative during the operation",
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
    return parser.parse_known_args(args, namespace)[0]


def get_default_servicer_config(
    cmdline: Optional[List[str]] = None,
) -> Tuple[ServicerConfig, ExtraFlags]:
    file = get_file_envs()
    envs = get_envs()
    args = parse_servicer_arguments(cmdline)
    cfgs = get_cfg_section_by_path(args.config) if args.config else dict()

    extra = ExtraFlags()
    extra.show_modules = args.list

    if args.module == SKIP_MODULE:
        args.module = None

    assert isinstance(args.opts, list)
    if not args.opts:
        # REMAINDER forces assignment with 'list'.
        # Remove to use 'opts' set in another namespace.
        args.opts = None

    result = right_join(
        typing_namespace(Namespace(**file), ServicerConfig),
        typing_namespace(Namespace(**envs), ServicerConfig),
        typing_namespace(Namespace(**cfgs), ServicerConfig),
        ServicerConfig(**vars(args)),
    )

    return result, extra
