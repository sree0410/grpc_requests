# grpc_requests
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/grpc-requests?style=flat-square)](https://pypi.org/project/grpc-requests)
[![PyPI](https://img.shields.io/pypi/v/grpc-requests?style=flat-square)](https://pypi.org/project/grpc-requests)
[![PyPI download month](https://img.shields.io/pypi/dm/grpc-requests?style=flat-square)](https://pypi.org/project/grpc-requests)
[![codecov](https://codecov.io/gh/spaceone-dev/grpc_requests/branch/master/graph/badge.svg)](https://codecov.io/gh/spaceone-dev/grpc_requests)
![Views](https://views.whatilearened.today/views/github/spaceone-dev/grpc_requests.svg)

##GRPC for Humans 


## Feature
- connect server using reflection
- no need stub class request grpc
- supprot method
    - [x] unary-unary
    - [x] unary-stream
    - [x] stream-unary
    - [x] stream-stream

## install
```shell script
pip install grpc_requests
```
    
## example
```python
from grpc_requests import Client

port = '50051'
host = "localhost"
endpoint = f"{host}:{port}"

client = Client.get_by_endpoint(endpoint)
print(client.service_names) # ["helloworld.Greeter"]

service = "helloworld.Greeter"
unary_unary_method = 'SayHello'

request_data = {"name": 'sinsky'} # You Don't Need Stub!
result = client.unary_unary(service, unary_unary_method, request_data)
assert dict == type(result) # result is dict Type!!! not Stub Object!
assert {"message":"Hellow sinsky"} == result

unary_stream_method = 'SayHelloGroup'
unary_stream_results = client.unary_stream(service, unary_unary_method, request_data)
assert all([dict == type(result) for result in unary_stream_results])
assert [{"message":"Hellow sinsky"}] == list(unary_stream_results)

request_datas = [request_data] # iterator

stream_unary_method = 'HelloEveryone'
result_stream_unary = client.stream_unary(service, stream_unary_method, request_datas)
assert dict == type(result) # result is dict Type!!! not Stub Object!

stream_stream_method = 'SayHelloOneByOne'
result = client.stream_stream(service, stream_stream_method,request_datas )
assert all([dict == type(result) for result in unary_stream_results])
```

## using Stub example
```python
from grpc_requests import Client
from helloworld_pb2 import HelloRequest

port = '50051'
host = "localhost"
endpoint = f"{host}:{port}"

client = Client.get_by_endpoint(endpoint)
print(client.service_names) # ["helloworld.Greeter"]

service = "helloworld.Greeter"
method = 'SayHello'

result = client.unary_unary(service, method, HelloRequest(name='sinsky'))
print(type(result)) # result is dict Type!!! not Stub Object!
print(result) # {"message":"Hellow sinsky"}

# or get raw response data
result = client.unary_unary(service, method, HelloRequest(name='sinsky'),raw_output=True)
print(type(result)) # HelloReply stub class

```


## Relation Project
- [homi](https://github.com/spaceone-dev/homi) : micro grpc framework like flask. easy to use!

## Change Logs
- 0.0.1
    - sync proto using reflection
    - auto convert request(response) from(to) dict
    - support unary-unary
- 0.0.2
    - support all method type
    - add request test case