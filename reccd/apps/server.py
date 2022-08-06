# -*- coding: utf-8 -*-

import os
import sys
from argparse import Namespace
from typing import Callable, List, Optional

from reccd.argparse.namespace_utils import right_join
from reccd.argparse.typing_namespace import typing_namespace
from reccd.arguments import SKIP_MODULE, get_default_server_namespace
from reccd.daemon.daemon_servicer import run_daemon_until_complete
from reccd.module.module import find_and_strip_module_prefix
from reccd.parse.cfg_parse import get_cfg_section_by_path
from reccd.parse.env_parse import get_envs, get_file_envs
from reccd.uri.rpc_uri import parse_rpc_address_as_class
from reccd.variables.system import EXIT_FALSE


class ServerConfig(Namespace):
    address: str
    module: Optional[str]
    opts: Optional[List[str]]


def get_default_server_config() -> ServerConfig:
    return ServerConfig(**vars(get_default_server_namespace()))


def get_server_config(args: Namespace) -> ServerConfig:
    k_config = "config"
    k_module = "module"
    k_opts = "opts"

    config_path = getattr(args, k_config, None)
    file = get_file_envs()
    envs = get_envs()
    cfgs = get_cfg_section_by_path(config_path) if config_path else dict()

    if hasattr(args, k_module):
        if getattr(args, k_module) == SKIP_MODULE:
            delattr(args, k_module)

    if hasattr(args, k_opts):
        # REMAINDER forces assignment with 'list'.
        # Remove to use 'opts' set in another namespace.
        if not getattr(args, k_opts):
            delattr(args, k_opts)

    return right_join(
        get_default_server_config(),
        typing_namespace(Namespace(**file), ServerConfig),
        typing_namespace(Namespace(**envs), ServerConfig),
        typing_namespace(Namespace(**cfgs), ServerConfig),
        ServerConfig(**vars(args)),
    )


_FIRST_ARGUMENT_ASSERTION_MESSAGE = (
    "The first argument on the command line is the path to the script file"
)


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    module_prefix = args.module_prefix
    assert isinstance(module_prefix, str)

    modules = find_and_strip_module_prefix(module_prefix)
    if not modules:
        printer("Not found modules")
        return EXIT_FALSE

    config = get_server_config(args)

    module_name = config.module
    if not module_name:
        printer("Empty module name")
        return EXIT_FALSE

    if module_name not in modules:
        printer("Not found module name")
        return EXIT_FALSE

    grpc_address = config.address
    try:
        # Test gRPC URL ...
        parse_rpc_address_as_class(grpc_address)
    except ValueError as e:
        printer(str(e))
        return EXIT_FALSE

    script_path = str(sys.argv[0])
    assert os.path.isfile(script_path), _FIRST_ARGUMENT_ASSERTION_MESSAGE

    sys.argv.clear()
    sys.argv.append(script_path)
    if config.opts:
        sys.argv += config.opts

    return run_daemon_until_complete(
        address=grpc_address,
        module=module_prefix + module_name,
        wait_connect=True,
    )
