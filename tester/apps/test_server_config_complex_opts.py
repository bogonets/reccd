# -*- coding: utf-8 -*-

from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from reccd.apps.server import get_server_config
from reccd.arguments import CMD_SERVER, SKIP_MODULE, get_default_arguments
from reccd.parse.env_parse import get_env, get_file_env
from reccd.system.environ import exchange_env
from reccd.variables.argparse import VALUE_SEPARATOR
from reccd.variables.config import (
    CFG_SECTION,
    ENVIRONMENT_FILE_PREFIX,
    ENVIRONMENT_FILE_SUFFIX,
    ENVIRONMENT_PREFIX,
    ENVIRONMENT_SUFFIX,
)


class ServerConfigComplexOptsTestCase(TestCase):

    RECCD_OPTS = f"{ENVIRONMENT_PREFIX}OPTS{ENVIRONMENT_SUFFIX}"
    RECCD_OPTS_FILE = f"{ENVIRONMENT_FILE_PREFIX}OPTS{ENVIRONMENT_FILE_SUFFIX}"

    def setUp(self):
        self.env_key = "opts"
        self.env_value = f"t1{VALUE_SEPARATOR}t2"
        self.env_original = exchange_env(self.RECCD_OPTS, self.env_value)
        self.assertEqual(self.env_value, get_env(self.env_key))

        self.tmpdir = TemporaryDirectory()
        self.secret_path = Path(self.tmpdir.name) / "secret"
        self.secret_value = f"t3{VALUE_SEPARATOR}t4"
        self.secret_path.write_text(self.secret_value)
        self.assertTrue(self.secret_path.exists())
        self.secret_original = exchange_env(
            self.RECCD_OPTS_FILE,
            str(self.secret_path),
        )
        self.assertEqual(self.secret_value, get_file_env(self.env_key))

        self.config_value = f"t5{VALUE_SEPARATOR}t6"
        self.config_path = Path(self.tmpdir.name) / "reccd.cfg"
        self.config_path.write_text(f"[{CFG_SECTION}]\nopts={self.config_value}")
        self.assertTrue(self.config_path.exists())

    def tearDown(self):
        exchange_env(self.RECCD_OPTS, self.env_original)
        exchange_env(self.RECCD_OPTS_FILE, self.secret_original)
        self.tmpdir.cleanup()
        self.assertFalse(self.secret_path.exists())
        self.assertFalse(self.config_path.exists())

    def test_module_attribute(self):
        args1 = get_default_arguments(
            [CMD_SERVER, "-c", str(self.config_path), "--", SKIP_MODULE, "t7", "t8"],
        )
        config1 = get_server_config(args1)
        self.assertIsNone(config1.module)
        self.assertListEqual(["t7", "t8"], config1.opts)

        args2 = get_default_arguments([CMD_SERVER, "-c", str(self.config_path)])
        config2 = get_server_config(args2)
        self.assertIsNone(config2.module)
        self.assertListEqual(["t5", "t6"], config2.opts)

        args3 = get_default_arguments([CMD_SERVER])
        config3 = get_server_config(args3)
        self.assertIsNone(config3.module)
        self.assertListEqual(["t1", "t2"], config3.opts)

        environ.pop(self.RECCD_OPTS)
        args4 = get_default_arguments([CMD_SERVER])
        config4 = get_server_config(args4)
        self.assertIsNone(config4.module)
        self.assertListEqual(["t3", "t4"], config4.opts)


if __name__ == "__main__":
    main()
