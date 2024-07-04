"""
SPDX-FileCopyrightText: 2024 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at

    http://www.apache.org/licenses/LICENSE-2.0

SPDX-License-Identifier: Apache-2.0
"""

import unittest

from uprotocol.communication.rpcresult import RpcResult
from uprotocol.v1.ucode_pb2 import UCode


class TestRpcResult(unittest.TestCase):
    def test_is_success_on_success(self):
        result = RpcResult.success(2)
        self.assertTrue(result.is_success())

    def test_is_success_on_failure(self):
        result = RpcResult.failure(code=UCode.INVALID_ARGUMENT, message="boom")
        self.assertFalse(result.is_success())

    def test_is_failure_on_success(self):
        result = RpcResult.success(2)
        self.assertFalse(result.is_failure())

    def test_is_failure_on_failure(self):
        result = RpcResult.failure(code=UCode.INVALID_ARGUMENT, message="boom")
        self.assertTrue(result.is_failure())

    def test_to_string_success(self):
        result = RpcResult.success(2)
        self.assertEqual(str(result), "Success(2)")

    def test_to_string_failure(self):
        result = RpcResult.failure(code=UCode.INVALID_ARGUMENT, message="boom")
        self.assertTrue(result.is_failure())
        self.assertEqual(result.failure_value().code, UCode.INVALID_ARGUMENT)
        self.assertEqual(result.failure_value().message, "boom")


if __name__ == '__main__':
    unittest.main()
