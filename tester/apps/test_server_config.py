# -*- coding: utf-8 -*-

from argparse import Namespace
from unittest import TestCase, main

from reccd.apps.server import get_server_config
from reccd.variables.rpc import DEFAULT_DAEMON_ADDRESS


class ServerConfigTestCase(TestCase):
    def test_get_server_config_01(self):
        args = get_server_config(Namespace())
        self.assertEqual(DEFAULT_DAEMON_ADDRESS, args.address)
        self.assertIsNone(args.module)
        self.assertIsNone(args.opts)

    def test_get_server_config_02(self):
        args = get_server_config(Namespace(module="module1", opts=["a", "b"]))
        self.assertEqual("module1", args.module)
        self.assertEqual(DEFAULT_DAEMON_ADDRESS, args.address)
        self.assertListEqual(["a", "b"], args.opts)

    def test_get_server_config_03(self):
        namespace = Namespace(address="0.0.0.0:8080", module="module2")
        args = get_server_config(namespace)
        self.assertEqual("module2", args.module)
        self.assertEqual("0.0.0.0:8080", args.address)
        self.assertIsNone(args.opts)


if __name__ == "__main__":
    main()
