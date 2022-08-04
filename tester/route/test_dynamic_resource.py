# -*- coding: utf-8 -*-

from unittest import TestCase, main

from reccd.route.dynamic_resource import DynamicResource


class DynamicResourceTestCase(TestCase):
    def test_static_path(self):
        res = DynamicResource("/v1/test")
        match0 = res.match("/v1/test")
        self.assertIsNotNone(match0)
        self.assertEqual(0, len(match0))

        match1 = res.match("/v1/tes")
        self.assertIsNone(match1)

        match2 = res.match("/v1/test/kkk")
        self.assertIsNone(match2)

    def test_dynamic_path(self):
        res = DynamicResource("/v1/{test}/test")
        match0 = res.match("/v1/test")
        self.assertIsNone(match0)

        match1 = res.match("/v1/aaa/test")
        self.assertIsNotNone(match1)
        self.assertEqual(1, len(match1))
        self.assertEqual("aaa", match1["test"])

    def test_dynamic_path_regex(self):
        res = DynamicResource("/v1/{value:[1-9]+}/test")
        match0 = res.match("/v1/test")
        self.assertIsNone(match0)

        match1 = res.match("/v1/1234/test")
        self.assertIsNotNone(match1)
        self.assertEqual(1, len(match1))
        self.assertEqual("1234", match1["value"])

        match2 = res.match("/v1/kkk/test")
        self.assertIsNone(match2)

        match3 = res.match("/v1/12a4/test")
        self.assertIsNone(match3)


if __name__ == "__main__":
    main()
