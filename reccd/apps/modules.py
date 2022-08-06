# -*- coding: utf-8 -*-

from argparse import Namespace
from io import StringIO
from typing import Callable, List

from reccd.logging.logging import reccd_logger as logger
from reccd.module.module import Module, find_and_strip_module_prefix


def printable_module_information(
    module_names: List[str],
    module_prefix: str,
    with_version=False,
    with_doc=False,
) -> str:
    buffer = StringIO()

    for module_name in module_names:
        module = Module(module_prefix + module_name, isolate=True)
        version = module.version
        doc = module.doc

        buffer.write(module_name)
        if with_version and version:
            buffer.write(f" ({version})")
        if with_doc and doc:
            buffer.write(f" - {doc}")
        buffer.write("\n")

    return buffer.getvalue().strip()


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    module_prefix = args.module_prefix
    verbose = args.verbose
    assert isinstance(module_prefix, str)
    assert isinstance(verbose, int)

    module_names = find_and_strip_module_prefix(module_prefix)
    with_version = verbose >= 1
    with_doc = verbose >= 2

    message = printable_module_information(
        module_names,
        module_prefix,
        with_version,
        with_doc,
    )

    logger.debug(f"List of modules (with_version={with_version},with_doc={with_doc})")
    if message:
        printer(message)

    return 0
