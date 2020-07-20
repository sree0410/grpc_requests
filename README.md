# grpc_requests
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/grpc_requests?style=flat-square)](https://pypi.org/project/grpc_requests)
[![PyPI](https://img.shields.io/pypi/v/grpc_requests?style=flat-square)](https://pypi.org/project/grpc_requests)
[![PyPI download month](https://img.shields.io/pypi/dm/grpc_requests?style=flat-square)](https://pypi.org/project/grpc_requests)
[![codecov](https://codecov.io/gh/spaceone-dev/grpc_requests/branch/master/graph/badge.svg)](https://codecov.io/gh/spaceone-dev/grpc_requests)
![Views](views.whatilearened.today/views/github/spaceone-dev/grpc_requests.svg)

##GRPC for Humans 


## Feature
- connect server using reflection
- no need stub class request grpc
- supprot method
    - [x] unary-unary
    - [ ] unary-stream
    - [ ] stream-unary
    - [ ] stream-stream

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
method = 'SayHello'

request_data = {"name": 'sinsky'} # You Don't Need Stub!
result = client.unary_unary(service, method, request_data)
print(type(result)) # result is dict Type!!! not Stub Object!
print(result) # {"message":"Hellow sinsky"}
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