from homi import App, Server, Service
from homi.extend.service import health_service, reflection_service

try:
    from .helloworld_pb2 import _GREETER
except Exception:
    from helloworld_pb2 import _GREETER

app = App(services=[reflection_service, health_service, ])

greeter = Service(_GREETER)


# unary-unary method
@greeter.method()
def SayHello(name, **kwargs):
    print(f"{name} is request SayHello")
    return {"message": f"Hello {name}!"}


# unary-stream method
@greeter.method()
def SayHelloGroup(name, **kwargs):
    print(f"{name} is request SayHelloGroup")
    names = ['a', 'b', 'c', 'd']
    for name in names:
        yield {"message": f"Hello {name}!"}


# stream-unary method
@greeter.method()
def HelloEveryone(request_iterator, context):
    names = []
    for reqs in request_iterator:
        print('you can get raw request', reqs.raw_data)
        names.append(reqs['name'])
    return {"message": f"Hello everyone {names}!"}


# stream-stream method
@greeter.method()
def SayHelloOneByOne(request_iterator, context):
    for req in request_iterator:
        name = req['name']
        print(f"{name} say to you hello")
        yield {"message": f"Hello {name}!"}


app.add_service(greeter)

if __name__ == '__main__':
    Server(app=app, worker=200).run()
