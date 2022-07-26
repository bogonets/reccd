# -*- coding: utf-8 -*-

from asyncio import sleep
from typing import Awaitable, Callable, Optional

from reccd.variables.aio import DEFAULT_RESTART_COUNT, DEFAULT_RESTART_DURATION


async def try_connection(
    predictor: Callable[[], Awaitable[bool]],
    retry_delay: Optional[float] = None,
    max_attempts: Optional[int] = None,
    *,
    try_cb: Callable[[int, int], None] = None,
    retry_cb: Callable[[int, int], None] = None,
    success_cb: Callable[[int, int], None] = None,
    failure_cb: Callable[[int, int], None] = None,
) -> bool:
    retry_seconds = retry_delay if retry_delay else DEFAULT_RESTART_DURATION
    retry_count = max_attempts if max_attempts else DEFAULT_RESTART_COUNT
    i = 0
    while i < retry_count:
        try:
            if try_cb:
                try_cb(i, retry_count)
            if await predictor():
                if success_cb:
                    success_cb(i, retry_count)
                return True
        except:  # noqa
            pass

        i += 1
        if i < retry_count:
            if retry_cb:
                retry_cb(i, retry_count)
            await sleep(retry_seconds)

    if failure_cb:
        failure_cb(i, retry_count)
    return False
