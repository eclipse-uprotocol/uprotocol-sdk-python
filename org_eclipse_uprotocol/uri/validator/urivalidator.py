# -------------------------------------------------------------------------
from org_eclipse_uprotocol.transport.datamodel.ustatus import UStatus, Code
# Copyright (c) 2023 General Motors GTO LLC

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# -------------------------------------------------------------------------

from org_eclipse_uprotocol.uri.datamodel.uresource import UResource
from org_eclipse_uprotocol.uri.datamodel.uuri import UUri


class UriValidator:
    @staticmethod
    def validate(uri: UUri) -> UStatus:
        if uri.is_empty():
            return UStatus.failed_with_msg_and_code("Uri is empty.", Code.INVALID_ARGUMENT)

        if uri.get_u_entity().name.strip() == "":
            return UStatus.failed_with_msg_and_code("Uri is missing uSoftware Entity name.", Code.INVALID_ARGUMENT)

        return UStatus.ok()

    @staticmethod
    def validate_rpc_method(uri: UUri) -> UStatus:
        status = UriValidator.validate(uri)
        if status.isFailed():
            return status

        u_resource = uri.get_u_resource()
        if not u_resource.is_rpc_method():
            return UStatus.failed_with_msg_and_code(
                "Invalid RPC method uri. Uri should be the method to be called, or method from response.",
                Code.INVALID_ARGUMENT)

        return UStatus.ok()

    @staticmethod
    def validate_rpc_response(uri: UUri) -> UStatus:
        status = UriValidator.validate(uri)
        if status.isFailed():
            return status

        u_resource = uri.get_u_resource()
        if not (u_resource.is_rpc_method() and u_resource.instance == UResource.for_rpc_response().instance):
            return UStatus.failed_with_msg_and_code("Invalid RPC response type.", Code.INVALID_ARGUMENT)

        return UStatus.ok()
