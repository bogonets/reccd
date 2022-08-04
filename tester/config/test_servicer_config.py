# -*- coding: utf-8 -*-

from unittest import TestCase, main

from reccd.config.servicer_config import get_default_servicer_config
from reccd.variables.rpc import DEFAULT_DAEMON_ADDRESS


class ServicerConfigTestCase(TestCase):
    def test_empty(self):
        args = get_default_servicer_config([])
        self.assertEqual(DEFAULT_DAEMON_ADDRESS, args.address)
        self.assertEqual(0, args.verbose)
        self.assertIsNone(args.module)
        self.assertIsNone(args.opts)

    def test_opts(self):
        args1 = get_default_servicer_config(["module1", "a", "b"])
        self.assertEqual("module1", args1.module)
        self.assertEqual(DEFAULT_DAEMON_ADDRESS, args1.address)
        self.assertEqual(0, args1.verbose)
        self.assertListEqual(["a", "b"], args1.opts)

        args2 = get_default_servicer_config(["-vvv", "-a", "0.0.0.0:8080", "module2"])
        self.assertEqual("module2", args2.module)
        self.assertEqual("0.0.0.0:8080", args2.address)
        self.assertEqual(3, args2.verbose)
        self.assertIsNone(args2.opts)


if __name__ == "__main__":
    main()
