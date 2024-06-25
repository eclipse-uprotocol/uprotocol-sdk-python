"""
SPDX-FileCopyrightText: 2024 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at

    http://www.apache.org/licenses/LICENSE-2.0

SPDX-License-Identifier: Apache-2.0
"""

from uprotocol.communication.requesthandler import RequestHandler
from uprotocol.communication.rpcserver import RpcServer
from uprotocol.communication.ustatuserror import UStatusError
from uprotocol.transport.builder.umessagebuilder import UMessageBuilder
from uprotocol.transport.ulistener import UListener
from uprotocol.transport.utransport import UTransport
from uprotocol.uri.factory.uri_factory import UriFactory
from uprotocol.v1.uattributes_pb2 import (
    UMessageType,
)
from uprotocol.v1.ucode_pb2 import UCode
from uprotocol.v1.umessage_pb2 import UMessage
from uprotocol.v1.uri_pb2 import UUri
from uprotocol.v1.ustatus_pb2 import UStatus


class HandleRequestListener(UListener):
    def __init__(self, transport: UTransport, request_handlers):
        self.transport = transport
        self.request_handlers = request_handlers

    def on_receive(self, request: UMessage) -> None:
        """
        Generic incoming handler to process RPC requests from clients.

        :param request: The request message from clients.
        """
        # Only handle request messages, ignore all other messages like notifications
        if request.attributes.type != UMessageType.UMESSAGE_TYPE_REQUEST:
            return

        request_attributes = request.attributes

        # Check if the request is for one that we have registered a handler for, if not ignore it
        handler = self.request_handlers.pop(request_attributes.sink, None)
        if handler is None:
            return

        response_builder = UMessageBuilder.response_for_request(request_attributes)

        try:
            response_payload = handler.handle_request(request)
        except Exception as e:
            code = UCode.INTERNAL
            response_payload = None
            if isinstance(e, UStatusError):
                code = e.get_status().get_code()
            response_builder.with_comm_status(code)

        self.transport.send(response_builder.build(response_payload))


class InMemoryRpcServer(RpcServer):
    def __init__(self, transport):
        if not transport:
            raise ValueError(UTransport.TRANSPORT_NULL_ERROR)
        elif not isinstance(transport, UTransport):
            raise ValueError(UTransport.TRANSPORT_NOT_INSTANCE_ERROR)
        self.transport = transport
        self.request_handlers = {}
        self.request_handler = HandleRequestListener(self.transport, self.request_handlers)

    def register_request_handler(self, method_uri: UUri, handler: RequestHandler) -> UStatus:
        """
        Register a handler that will be invoked when requests come in from clients for the given method.

        Note: Only one handler is allowed to be registered per method URI.

        :param method_uri: The URI for the method to register the listener for.
        :param handler: The handler that will process the request for the client.
        :return: Returns the status of registering the RpcListener.
        """
        if method_uri is None:
            raise ValueError("Method URI missing")
        if handler is None:
            raise ValueError("Request listener missing")

        # Ensure the method URI matches the transport source URI
        if (
            method_uri.authority_name != self.transport.get_source().authority_name
            or method_uri.ue_id != self.transport.get_source().ue_id
            or method_uri.ue_version_major != self.transport.get_source().ue_version_major
        ):
            raise UStatusError.from_code_message(
                UCode.INVALID_ARGUMENT, "Method URI does not match the transport source URI"
            )

        try:
            if method_uri in self.request_handlers:
                current_handler = self.request_handlers[method_uri]
                if current_handler is not None:
                    raise UStatusError.from_code_message(UCode.ALREADY_EXISTS, "Handler already registered")

            result = self.transport.register_listener(UriFactory.ANY, self.request_handler, method_uri)
            if result.code != UCode.OK:
                raise UStatusError.from_code_message(result.code, result.message)

            self.request_handlers[method_uri] = handler
            return UStatus(UCode.OK)

        except UStatusError as e:
            return UStatus(code=e.get_code(), message=e.get_message())
        except Exception as e:
            return UStatus(UCode.INTERNAL, str(e))

    def unregister_request_handler(self, method_uri: UUri, handler: RequestHandler) -> UStatus:
        """
        Unregister a handler that will be invoked when requests come in from clients for the given method.

        :param method_uri: The resolved UUri where the listener was registered to receive messages from.
        :param handler: The handler for processing requests.
        :return: Returns the status of unregistering the RpcListener.
        """
        if method_uri is None:
            raise ValueError("Method URI missing")
        if handler is None:
            raise ValueError("Request listener missing")

        # Ensure the method URI matches the transport source URI
        if (
            method_uri.authority_name != self.transport.get_source().authority_name
            or method_uri.ue_id != self.transport.get_source().ue_id
            or method_uri.ue_version_major != self.transport.get_source().ue_version_major
        ):
            raise UStatusError.from_code_message(
                UCode.INVALID_ARGUMENT, "Method URI does not match the transport source URI"
            )

        if self.request_handlers.get(method_uri) == handler:
            del self.request_handlers[method_uri]
            return self.transport.unregister_listener(UriFactory.ANY, self.request_handler, method_uri)

        return UStatus(code=UCode.NOT_FOUND)
