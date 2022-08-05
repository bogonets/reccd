# -*- coding: utf-8 -*-

from typing import Callable, List, Optional

from reccd.apps.client import main as client_main
from reccd.apps.modules import main as modules_main
from reccd.apps.server import main as server_main
from reccd.arguments import CMD_CLIENT, CMD_MODULES, CMD_SERVER, get_default_arguments
from reccd.logging.logging import SEVERITY_NAME_DEBUG
from reccd.logging.logging import reccd_logger as logger
from reccd.logging.logging import (
    set_default_logging_config,
    set_root_level,
    set_simple_logging_config,
)


def main(
    cmdline: Optional[List[str]] = None,
    printer: Callable[..., None] = print,
) -> int:
    args = get_default_arguments(cmdline)

    cmd = args.cmd
    default_logging = args.default_logging
    simple_logging = args.simple_logging
    severity = args.severity
    debug = args.debug
    verbose = args.verbose

    if not cmd:
        printer("The command does not exist")
        return 1

    if default_logging and simple_logging:
        printer(
            "The 'default_logging' flag and the 'simple_logging' flag cannot coexist"
        )
        return 1

    assert cmd in [CMD_CLIENT, CMD_MODULES, CMD_SERVER]
    assert isinstance(default_logging, bool)
    assert isinstance(simple_logging, bool)
    assert isinstance(severity, str)
    assert isinstance(debug, bool)
    assert isinstance(verbose, int)

    if default_logging:
        set_default_logging_config()
    elif simple_logging:
        set_simple_logging_config()

    if debug:
        set_root_level(SEVERITY_NAME_DEBUG)
    else:
        set_root_level(severity)

    logger.debug(f"Arguments: {args}")

    if cmd == CMD_CLIENT:
        return client_main(args, printer=printer)
    elif cmd == CMD_MODULES:
        return modules_main(args, printer=printer)
    elif cmd == CMD_SERVER:
        return server_main(args, printer=printer)
    else:
        assert False, "Inaccessible section"


if __name__ == "__main__":
    exit(main())
