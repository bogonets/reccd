# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import run as asyncio_run
from typing import Callable

from reccd.arguments import KV_SEPARATOR
from reccd.daemon.daemon_client import DaemonClient
from reccd.logging.logging import reccd_logger as logger
from reccd.variables.rpc import DEFAULT_HEARTBEAT_DELAY
from reccd.variables.system import EXIT_EXCEPTION, EXIT_FALSE, EXIT_TRUE


async def async_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    logger.debug(f"Arguments: {args}")
    heartbeat_delay = DEFAULT_HEARTBEAT_DELAY
    default_logging = args.default_logging
    simple_logging = args.simple_logging
    heartbeat = args.heartbeat
    skip_heartbeat = args.skip_heartbeat
    register = args.register
    skip_register = args.skip_register
    timeout = args.timeout
    disable_shared_memory = args.disable_shared_memory
    address = args.address
    method = args.method
    path = args.path
    keyword = args.keyword
    request_args = args.args
    verbose = args.verbose

    assert isinstance(default_logging, bool)
    assert isinstance(simple_logging, bool)
    assert isinstance(heartbeat, bool)
    assert isinstance(skip_heartbeat, bool)
    assert isinstance(register, bool)
    assert isinstance(skip_register, bool)
    assert isinstance(timeout, float)
    assert isinstance(disable_shared_memory, bool)
    assert isinstance(address, str)
    assert isinstance(method, str)
    assert isinstance(path, str)
    assert isinstance(keyword, (list, type(None)))
    assert isinstance(request_args, list)
    assert isinstance(verbose, int)

    if heartbeat and skip_heartbeat:
        raise ValueError(
            "The 'heartbeat' flag and the 'skip_heartbeat' flag cannot coexist"
        )
    if register and skip_register:
        raise ValueError(
            "The 'register' flag and the 'skip_register' flag cannot coexist"
        )

    client = DaemonClient(
        address,
        timeout=timeout,
        disable_shared_memory=disable_shared_memory,
        verbose=verbose,
    )

    logger.debug("Opening client ...")
    await client.open()
    logger.info("Opened client")

    try:
        if not skip_heartbeat:
            logger.debug(f"HeartbeatQ(delay={heartbeat_delay}s) ...")
            heartbeat_answer = await client.heartbeat(delay=heartbeat_delay)
            heartbeat_message = f"HeartbeatA({heartbeat_answer})"
            if heartbeat_answer:
                logger.info(heartbeat_message)
            else:
                logger.warning(heartbeat_message)
            if heartbeat:
                return EXIT_TRUE if heartbeat_answer else EXIT_FALSE

        if not skip_register:
            logger.debug("RegisterQ() ...")
            register_answer = await client.register()
            register_message = f"RegisterA({register_answer})"
            if register_answer == 0:
                logger.info(register_message)
            else:
                logger.warning(register_message)
            if register:
                return register_answer

        kwargs = dict()
        if keyword:
            for x in keyword:
                assert isinstance(x, str)
                kv = x.split(KV_SEPARATOR)
                if len(kv) != 2:
                    raise ValueError(f"Invalid keyword argument: {x}")
                kwargs[kv[0]] = kv[1]

        params = f"method={method},path={path},args={request_args},kwargs={kwargs}"
        logger.debug(f"RequestQ({params}) ...")

        request_answer = await client.request(method, path, *request_args, **kwargs)

        response_args = request_answer.to_args_str()
        response_kwargs = request_answer.to_kwargs_str()

        printer(f"Response positional arguments: {response_args}")
        printer(f"Response keyword arguments: {response_kwargs}")
    finally:
        logger.debug("Closing client ...")
        await client.close()
        logger.info("Closed client")

    return EXIT_TRUE


def main(args: Namespace, printer: Callable[..., None] = print) -> int:
    try:
        return asyncio_run(async_main(args, printer))
    except BaseException as e:
        logger.exception(e)
        return EXIT_EXCEPTION
