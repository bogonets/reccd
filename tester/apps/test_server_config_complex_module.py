# -*- coding: utf-8 -*-

from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from reccd.apps.server import get_server_config
from reccd.arguments import CMD_SERVER, get_default_arguments
from reccd.parse.env_parse import get_env, get_file_env
from reccd.system.environ import exchange_env
from reccd.variables.config import (
    CFG_SECTION,
    ENVIRONMENT_FILE_PREFIX,
    ENVIRONMENT_FILE_SUFFIX,
    ENVIRONMENT_PREFIX,
    ENVIRONMENT_SUFFIX,
)


class ServerConfigComplexModuleTestCase(TestCase):

    RECCD_MODULE = f"{ENVIRONMENT_PREFIX}MODULE{ENVIRONMENT_SUFFIX}"
    RECCD_MODULE_FILE = f"{ENVIRONMENT_FILE_PREFIX}MODULE{ENVIRONMENT_FILE_SUFFIX}"

    def setUp(self):
        self.env_key = "module"
        self.env_value = "test1"
        self.env_original = exchange_env(self.RECCD_MODULE, self.env_value)
        self.assertEqual(self.env_value, get_env(self.env_key))

        self.tmpdir = TemporaryDirectory()
        self.secret_path = Path(self.tmpdir.name) / "secret"
        self.secret_value = "test2"
        self.secret_path.write_text(self.secret_value)
        self.assertTrue(self.secret_path.exists())
        self.secret_original = exchange_env(
            self.RECCD_MODULE_FILE,
            str(self.secret_path),
        )
        self.assertEqual(self.secret_value, get_file_env(self.env_key))

        self.config_value = "test3"
        self.config_path = Path(self.tmpdir.name) / "reccd.cfg"
        self.config_path.write_text(f"[{CFG_SECTION}]\nmodule={self.config_value}")
        self.assertTrue(self.config_path.exists())

        self.args_value = "test4"

    def tearDown(self):
        exchange_env(self.RECCD_MODULE, self.env_original)
        exchange_env(self.RECCD_MODULE_FILE, self.secret_original)
        self.tmpdir.cleanup()
        self.assertFalse(self.secret_path.exists())
        self.assertFalse(self.config_path.exists())

    def test_module_attribute(self):
        args1 = get_default_arguments(
            [CMD_SERVER, "-c", str(self.config_path), self.args_value],
        )
        config1 = get_server_config(args1)
        self.assertEqual(self.args_value, config1.module)

        args2 = get_default_arguments([CMD_SERVER, "-c", str(self.config_path)])
        config2 = get_server_config(args2)
        self.assertEqual(self.config_value, config2.module)

        args3 = get_default_arguments([CMD_SERVER])
        config3 = get_server_config(args3)
        self.assertEqual(self.env_value, config3.module)

        environ.pop(self.RECCD_MODULE)
        args4 = get_default_arguments([CMD_SERVER])
        config4 = get_server_config(args4)
        self.assertEqual(self.secret_value, config4.module)


if __name__ == "__main__":
    main()
