# -*- coding: utf-8 -*-

import sys
from io import StringIO
from typing import Callable, List, Optional

from reccd.config.servicer_config import get_default_servicer_config
from reccd.daemon.daemon_servicer import run_daemon_until_complete
from reccd.logging.logging import set_default_logging_config, set_root_level
from reccd.module.module import Module
from reccd.package.package_utils import filter_module_names
from reccd.variables.module import MODULE_NAME_PREFIX


def find_and_strip_module_prefix(module_name_prefix=MODULE_NAME_PREFIX) -> List[str]:
    modules = filter_module_names(module_name_prefix)
    module_name_begin = len(module_name_prefix)
    return list(map(lambda x: x[module_name_begin:].strip(), modules))


def print_module_information(
    module_names: List[str],
    printer: Callable[..., None] = print,
) -> None:
    buffer = StringIO()

    for module_name in module_names:
        module = Module(module_name, isolate=True)
        version = module.version
        doc = module.doc

        buffer.write(module_name)
        if version:
            buffer.write(f" ({version})")
        if doc:
            buffer.write(f" - {doc}")
        buffer.write("\n")

    message = buffer.getvalue().strip()
    if message:
        printer(message)


def main(
    cmdline: Optional[List[str]] = None,
    printer: Callable[..., None] = print,
    module_name_prefix=MODULE_NAME_PREFIX,
) -> int:
    config, extra = get_default_servicer_config(cmdline)

    set_default_logging_config()
    if config.verbose >= 1:
        set_root_level("DEBUG")
    else:
        set_root_level("INFO")

    module_names = find_and_strip_module_prefix(module_name_prefix)

    if extra.show_modules:
        print_module_information(module_names, printer)
        return 0

    if not config.module:
        printer("Empty module name")
        return 1

    module_name = config.module
    if module_name not in module_names:
        printer("Not found module name")
        return 1

    sys.argv.clear()
    if config.opts:
        sys.argv += config.opts

    config.module = module_name_prefix + module_name
    return run_daemon_until_complete(config)


if __name__ == "__main__":
    exit(main())
