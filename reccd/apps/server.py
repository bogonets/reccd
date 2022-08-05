# -*- coding: utf-8 -*-

import sys
from argparse import Namespace
from typing import Callable, List, Optional

from reccd.argparse.namespace_utils import right_join
from reccd.argparse.typing_namespace import typing_namespace
from reccd.arguments import SKIP_MODULE
from reccd.daemon.daemon_servicer import run_daemon_until_complete
from reccd.module.module import find_and_strip_module_prefix
from reccd.parse.cfg_parse import get_cfg_section_by_path
from reccd.parse.env_parse import get_envs, get_file_envs
from reccd.variables.rpc import DEFAULT_DAEMON_ADDRESS

KEY_ADDRESS = "address"
KEY_CONFIG = "config"
KEY_MODULE = "module"
KEY_OPTS = "opts"


class ServerConfig(Namespace):
    address: str
    module: Optional[str]
    opts: Optional[List[str]]


def get_default_config() -> ServerConfig:
    return ServerConfig(address=DEFAULT_DAEMON_ADDRESS)


def get_server_config(args: Namespace) -> ServerConfig:
    config_path = getattr(args, KEY_CONFIG, None)
    file = get_file_envs()
    envs = get_envs()
    cfgs = get_cfg_section_by_path(config_path) if config_path else dict()

    if hasattr(args, KEY_MODULE):
        if getattr(args, KEY_MODULE) == SKIP_MODULE:
            delattr(args, KEY_MODULE)

    if hasattr(args, KEY_OPTS):
        # REMAINDER forces assignment with 'list'.
        # Remove to use 'opts' set in another namespace.
        if not getattr(args, KEY_OPTS):
            delattr(args, KEY_OPTS)

    return right_join(
        get_default_config(),
        typing_namespace(Namespace(**file), ServerConfig),
        typing_namespace(Namespace(**envs), ServerConfig),
        typing_namespace(Namespace(**cfgs), ServerConfig),
        ServerConfig(**vars(args)),
    )


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    module_prefix = args.module_prefix
    assert isinstance(module_prefix, str)

    modules = find_and_strip_module_prefix(module_prefix)
    if not modules:
        raise ModuleNotFoundError("Not found modules")

    config = get_server_config(args)

    if not config.module:
        printer("Empty module name")
        return 1

    module = config.module
    if module not in modules:
        printer("Not found module name")
        return 1

    script_path = str(sys.argv[0])
    sys.argv.clear()
    sys.argv.append(script_path)
    if config.opts:
        sys.argv += config.opts

    return run_daemon_until_complete(
        address=config.address,
        module=module_prefix + config.module,
        wait_connect=True,
    )
