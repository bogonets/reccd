# -*- coding: utf-8 -*-

from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from reccd.config.env_parse import get_env, get_file_env
from reccd.config.servicer_config import get_default_servicer_config
from reccd.system.environ import exchange_env
from reccd.variables.config import (
    CFG_SECTION,
    ENVIRONMENT_FILE_PREFIX,
    ENVIRONMENT_FILE_SUFFIX,
    ENVIRONMENT_PREFIX,
    ENVIRONMENT_SUFFIX,
    SKIP_MODULE,
    VALUE_SEPARATOR,
)


class ServicerConfigComplexModuleTestCase(TestCase):

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
        args1 = get_default_servicer_config(
            ["-c", str(self.config_path), self.args_value],
        )
        self.assertEqual(self.args_value, args1.module)

        args2 = get_default_servicer_config(["-c", str(self.config_path)])
        self.assertEqual(self.config_value, args2.module)

        args3 = get_default_servicer_config([])
        self.assertEqual(self.env_value, args3.module)

        environ.pop(self.RECCD_MODULE)
        args4 = get_default_servicer_config([])
        self.assertEqual(self.secret_value, args4.module)


class ServicerConfigComplexOptsTestCase(TestCase):

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
        args1 = get_default_servicer_config(
            ["-c", str(self.config_path), "--", SKIP_MODULE, "t7", "t8"],
        )
        self.assertIsNone(args1.module)
        self.assertListEqual(["t7", "t8"], args1.opts)

        args2 = get_default_servicer_config(["-c", str(self.config_path)])
        self.assertIsNone(args2.module)
        self.assertListEqual(["t5", "t6"], args2.opts)

        args3 = get_default_servicer_config([])
        self.assertIsNone(args3.module)
        self.assertListEqual(["t1", "t2"], args3.opts)

        environ.pop(self.RECCD_OPTS)
        args4 = get_default_servicer_config([])
        self.assertIsNone(args4.module)
        self.assertListEqual(["t3", "t4"], args4.opts)


if __name__ == "__main__":
    main()
