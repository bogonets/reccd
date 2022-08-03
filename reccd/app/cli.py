# -*- coding: utf-8 -*-

from reccd.config.servicer_config import get_default_servicer_config


def main() -> int:
    get_default_servicer_config()
    return 0


if __name__ == "__main__":
    exit(main())
