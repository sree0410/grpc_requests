import logging
from functools import partial
from typing import NamedTuple, Any, Dict, Set

import grpc
from google.protobuf import symbol_database as _symbol_database, descriptor_pool as _descriptor_pool, descriptor_pb2
from google.protobuf.json_format import MessageToDict, ParseDict
from grpc_reflection.v1alpha import reflection_pb2_grpc, reflection_pb2


class DescriptorImport:
    def __init__(self, ):
        pass


def make_request(*requests):
    for r in requests:
        yield r


def reflection_request(channel, requests):
    stub = reflection_pb2_grpc.ServerReflectionStub(channel)
    responses = stub.ServerReflectionInfo(make_request(requests))
    try:
        for resp in responses:
            yield resp
    except grpc._channel._Rendezvous as err:
        print(err)


_clients = {}


class BaseClient:
    def __init__(self, endpoint, symbol_db=None, descriptor_pool=None):
        self.endpoint = endpoint
        self._symbol_db = symbol_db or _symbol_database.Default()
        self._desc_pool = descriptor_pool or _descriptor_pool.Default()
        self._channel = grpc.insecure_channel(endpoint)

    @property
    def channel(self):
        return self._channel

    @classmethod
    def get_by_endpoint(cls, endpoint, **kwargs):
        if endpoint not in _clients:
            _clients[endpoint] = cls(endpoint, **kwargs)
        return _clients[endpoint]


class MethodDataType(NamedTuple):
    input_type: Any
    output_type: Any


class ReflectionClient(BaseClient):

    def __init__(self, endpoint, symbol_db=None, descriptor_pool=None, lazy=False):
        super().__init__(endpoint, symbol_db, descriptor_pool)
        self._service_names: list = None
        self._support_methods: Dict[str, Set[str]] = {}
        self.reflection_stub = reflection_pb2_grpc.ServerReflectionStub(self.channel)
        self.registered_file_names = set()
        self.has_server_registered = False
        self._services_module_name = {}

        self.methods_data_type: Dict[str, MethodDataType] = {}
        self._unary_unary_handler = {}
        self._unary_stream_handler = {}
        self._stream_unary_handler = {}
        self._stream_stream_handler = {}

        if not lazy:
            self.register_services_proto()

    def _reflection_request(self, *requests):
        responses = self.reflection_stub.ServerReflectionInfo((r for r in requests))
        return responses

    def _reflection_single_request(self, request):
        results = list(self._reflection_request(request))
        if len(results) > 1:
            raise ValueError('response have more then one result')
        return results[0]

    def _get_service_names(self):
        request = reflection_pb2.ServerReflectionRequest(list_services="")
        resp = self._reflection_single_request(request)
        services = tuple([s.name for s in resp.list_services_response.service])
        self._support_methods = {s: set() for s in services}
        return services

    def _get_file_descriptor_by_name(self, name):
        request = reflection_pb2.ServerReflectionRequest(file_by_filename=name)
        result = self._reflection_single_request(request)
        proto = result.file_descriptor_response.file_descriptor_proto[0]
        return descriptor_pb2.FileDescriptorProto.FromString(proto)

    def _get_file_descriptor_by_symbol(self, symbol):
        request = reflection_pb2.ServerReflectionRequest(file_containing_symbol=symbol)
        result = self._reflection_single_request(request)
        proto = result.file_descriptor_response.file_descriptor_proto[0]
        return descriptor_pb2.FileDescriptorProto.FromString(proto)

    def _register_file_descriptor(self, file_descriptor):
        logging.debug(f"start {file_descriptor.name} register")
        dependencies = list(file_descriptor.dependency)
        logging.debug(f"find {len(dependencies)} dependency in {file_descriptor.name}")
        for dep_file_name in dependencies:
            if dep_file_name not in self.registered_file_names:
                dep_desc = self._get_file_descriptor_by_name(dep_file_name)
                self._register_file_descriptor(dep_desc)
                self.registered_file_names.add(dep_file_name)
            else:
                logging.debug(f'{dep_file_name} already registered')

        self._desc_pool.Add(file_descriptor)
        logging.debug(f"end {file_descriptor.name} register")

    def check_method_available(self, service, method):
        if not self.has_server_registered:
            self.register_services_proto()

        if service not in self._support_methods:
            raise ValueError(
                f"{self.endpoint} server doesn't support {service}. Available services {self.service_names}")

        if method not in self._support_methods[service]:
            raise ValueError(
                f"{service} doesn't support {method} method. Available methods {self._support_methods[service]}")
        return True

    def register_services_proto(self):
        for service in self.service_names:
            logging.debug(f"start {service} register")
            file_descriptor = self._get_file_descriptor_by_symbol(service)
            self._register_file_descriptor(file_descriptor)
            self._support_methods[service] = set(self.get_service_descriptor(service).methods_by_name.keys())
            logging.debug(f"end {service} register")
        self.has_server_registered = True

    @property
    def service_names(self):
        if self._service_names is None:
            self._service_names = self._get_service_names()
        return self._service_names

    def _make_method_full_name(self, service, method):
        return f"/{service}/{method}"

    def _register_handler(self, method_type: str, service: str, method: str):
        method_full_name = self._make_method_full_name(service, method)
        handler_map = getattr(self, f"_{method_type}_handler")
        method_register_func = getattr(self.channel, method_type)
        handler_map[method_full_name] = method_register_func(**self.make_handler_argument(service, method))

    def _parse_input(self, data, input_type):
        _data = data or {}
        if isinstance(_data, dict):
            input = ParseDict(_data, input_type())
        else:
            input = _data
        return input

    def _parse_stream_input(self, datas, input_type):
        for data in datas:
            _data = data or {}
            yield self._parse_input(_data, input_type)

    def _parse_output(self, result):
        return MessageToDict(result)

    def _parse_stream_output(self, results):
        for result in results:
            yield self._parse_output(result)

    def unary_unary(self, service, method, data=None, raw_output=False):
        self.check_method_available(service, method)
        name = self._make_method_full_name(service, method)
        dtype = self.get_method_data_type(service, method)

        if name not in self._unary_unary_handler:
            self._register_handler('unary_unary', service, method)

        result = self._unary_unary_handler[name](self._parse_input(data, dtype.input_type))
        if raw_output:
            return result
        else:
            return self._parse_output(result)

    def unary_stream(self, service, method, data=None, raw_output=False):
        self.check_method_available(service, method)
        name = self._make_method_full_name(service, method)
        dtype = self.get_method_data_type(service, method)

        if name not in self._unary_stream_handler:
            self._register_handler('unary_stream', service, method)

        results = self._unary_stream_handler[name](self._parse_input(data, dtype))
        if raw_output:
            return results
        else:
            return self._parse_stream_output(results)

    def stream_unary(self, service, method, datas, raw_output=False):
        self.check_method_available(service, method)
        name = self._make_method_full_name(service, method)
        dtype = self.get_method_data_type(service, method)

        if name not in self._stream_unary_handler:
            self._register_handler('stream_unary', service, method)

        result = self._stream_unary_handler[name](self._parse_stream_input(datas, dtype.input_type))
        if raw_output:
            return result
        else:
            return self._parse_output(result)

    def stream_stream(self, service, method, datas, raw_output=False):
        self.check_method_available(service, method)
        name = self._make_method_full_name(service, method)
        dtype = self.get_method_data_type(service, method)

        if name not in self._stream_stream_handler:
            self._register_handler('stream_stream', service, method)

        results = self._stream_stream_handler[name](self._parse_stream_input(datas, dtype))
        if raw_output:
            return results
        else:
            return self._parse_stream_output(results)

    def get_service_descriptor(self, service):
        return self._desc_pool.FindServiceByName(service)

    def get_method_descriptor(self, service, method):
        svc_desc = self.get_service_descriptor(service)
        return svc_desc.FindMethodByName(method)

    def get_method_data_type(self, service: str, method: str) -> MethodDataType:
        method_name = self._make_method_full_name(service, method)
        if method_name not in self.methods_data_type:
            method_desc = self.get_method_descriptor(service, method)
            method_dtype = MethodDataType(
                self._symbol_db.GetPrototype(method_desc.input_type),
                self._symbol_db.GetPrototype(method_desc.output_type),
            )
            self.methods_data_type[method_name] = method_dtype
        return self.methods_data_type[method_name]

    def make_handler_argument(self, service: str, method: str):
        data_type = self.get_method_data_type(service, method)
        return {
            'method': self._make_method_full_name(service, method),
            'request_serializer': data_type.input_type.SerializeToString,
            'response_deserializer': data_type.output_type.FromString,
        }

    def service(self, name):
        if name in self.service_names:
            return ServiceClient(client=self, service_name=name)
        else:
            raise ValueError(f"{name} doesn't support. Available service {self.service_names}")


class ServiceClient:
    def __init__(self, client: ReflectionClient, service_name: str):
        self.client = client
        self.service_name = service_name
        self.method_names = tuple(self.client.get_service_descriptor(self.service_name).methods_by_name.keys())

        pass

    def __getattr__(self, item):
        if item in self.method_names:
            return partial(self.client.unary_unary, self.service_name, item)
        else:
            raise ValueError(f"{item} doesn't support. Available methods {self.method_names}")


Client = ReflectionClient
