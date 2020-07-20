import homi

from . import helloworld_pb2
from . import helloworld_pb2_grpc


# unary-unary method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return helloworld_pb2.HelloReply(message=f"Hello {name}!")


# unary-stream method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHelloGroup(name, **kwargs):
    print(f"{name} is request SayHelloGroup")
    names = ['a', 'b', 'c', 'd']
    for name in names:
        yield helloworld_pb2.HelloReply(message=f"Hello {name}!")


# stream-unary method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def HelloEveryone(request_iterator, context):
    names = []
    for reqs in request_iterator:
        print('you can get raw request', reqs.raw_data)
        names.append(reqs['name'])
    return helloworld_pb2.HelloReply(message=f"Hello everyone {names}!")


# stream-stream method
@homi.register(helloworld_pb2_grpc, 'Greeter')
def SayHelloOneByOne(request_iterator, context):
    for req in request_iterator:
        name = req['name']
        print(f"{name} say to you hello")
        yield helloworld_pb2.HelloReply(message=f"Hello {name}!")
