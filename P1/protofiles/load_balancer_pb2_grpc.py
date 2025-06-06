# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import load_balancer_pb2 as load__balancer__pb2

GRPC_GENERATED_VERSION = '1.70.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in load_balancer_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class LoadBalancerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetServer = channel.unary_unary(
                '/load_balancer.LoadBalancer/GetServer',
                request_serializer=load__balancer__pb2.ClientRequest.SerializeToString,
                response_deserializer=load__balancer__pb2.ServerResponse.FromString,
                _registered_method=True)
        self.RegisterServer = channel.unary_unary(
                '/load_balancer.LoadBalancer/RegisterServer',
                request_serializer=load__balancer__pb2.ServerRegistration.SerializeToString,
                response_deserializer=load__balancer__pb2.RegistrationResponse.FromString,
                _registered_method=True)
        self.ReportLoad = channel.unary_unary(
                '/load_balancer.LoadBalancer/ReportLoad',
                request_serializer=load__balancer__pb2.LoadReport.SerializeToString,
                response_deserializer=load__balancer__pb2.LoadReportResponse.FromString,
                _registered_method=True)


class LoadBalancerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RegisterServer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReportLoad(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_LoadBalancerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetServer': grpc.unary_unary_rpc_method_handler(
                    servicer.GetServer,
                    request_deserializer=load__balancer__pb2.ClientRequest.FromString,
                    response_serializer=load__balancer__pb2.ServerResponse.SerializeToString,
            ),
            'RegisterServer': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterServer,
                    request_deserializer=load__balancer__pb2.ServerRegistration.FromString,
                    response_serializer=load__balancer__pb2.RegistrationResponse.SerializeToString,
            ),
            'ReportLoad': grpc.unary_unary_rpc_method_handler(
                    servicer.ReportLoad,
                    request_deserializer=load__balancer__pb2.LoadReport.FromString,
                    response_serializer=load__balancer__pb2.LoadReportResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'load_balancer.LoadBalancer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('load_balancer.LoadBalancer', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class LoadBalancer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/load_balancer.LoadBalancer/GetServer',
            load__balancer__pb2.ClientRequest.SerializeToString,
            load__balancer__pb2.ServerResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def RegisterServer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/load_balancer.LoadBalancer/RegisterServer',
            load__balancer__pb2.ServerRegistration.SerializeToString,
            load__balancer__pb2.RegistrationResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ReportLoad(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/load_balancer.LoadBalancer/ReportLoad',
            load__balancer__pb2.LoadReport.SerializeToString,
            load__balancer__pb2.LoadReportResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)


class BackendStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ProcessTask = channel.unary_unary(
                '/load_balancer.Backend/ProcessTask',
                request_serializer=load__balancer__pb2.TaskRequest.SerializeToString,
                response_deserializer=load__balancer__pb2.TaskResponse.FromString,
                _registered_method=True)


class BackendServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ProcessTask(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BackendServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ProcessTask': grpc.unary_unary_rpc_method_handler(
                    servicer.ProcessTask,
                    request_deserializer=load__balancer__pb2.TaskRequest.FromString,
                    response_serializer=load__balancer__pb2.TaskResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'load_balancer.Backend', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('load_balancer.Backend', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Backend(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ProcessTask(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/load_balancer.Backend/ProcessTask',
            load__balancer__pb2.TaskRequest.SerializeToString,
            load__balancer__pb2.TaskResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
