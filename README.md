# reccd

![PyPI](https://img.shields.io/pypi/v/reccd?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/reccd?style=flat-square)
![GitHub](https://img.shields.io/github/license/bogonets/reccd?style=flat-square)

Daemon helper for the ANSWER

## About

A wrapper to easily adapt [gRPC](https://grpc.io/) communication without implementing [protobuf](https://protobuf.dev/).

## Usage

Print help message:
```shell
python -m reccd --help
```

Print version number:
```shell
python -m reccd --version
```

Prints a list of available modules:
```shell
python -m reccd -vvv modules
```

Start the gRPC daemon server:
```shell
python -m reccd -l -d -vvv server -a 0.0.0.0:8080 template
```

If you need to pass the module's arguments (`sys.argv`):
```shell
python -m reccd -l -d -vvv server -a 0.0.0.0:8080 template {argv1} {argv2} ... {argvN}
```

Communicates with the daemon server:
```shell
python -m reccd -l -d -vvv client -a 0.0.0.0:8080 -m post -p /echo message
```

### Change module prefix

The default module prefix is `reccd_`. If you want to change it, you can use the `--module-prefix` flag.

```shell
./python -m reccd --module-prefix 'my_prefix_' modules
```

## How to create a module

Create a project so that the package name starts with `reccd_`.

All specifications must be implemented in an `__init__.py` file at the root of the module.

### Module Version

Add the module's version. Must follow the [SemVer](https://semver.org/) specification.

```python
__version__ = "0.0.0"
```

### Module Documentation

Add documentation explaining how to use the module.

```python
__doc__ = """
Usage: module {arg0} {arg1}
...
"""
```

### Module Open Event

Implement the module's initialization event.

Command line arguments passed to the module can be accessed as `sys.argv`.

```python
async def on_open() -> None:
    pass
```

### Module Close Event

Implement the module's shutdown event.

```python
async def on_close() -> None:
    pass
```

### Module Register Event

Created to identify clients that will communicate with the module.

Arguments depend on the client implementation.

Returns `0` if registered successfully.

```python
async def on_register(*args, **kwargs) -> int:
    return 0
```

### Define the module's routing table

Check out [test](tester/unittest/modules/reccd_test_router/__init__.py) file.

```python
async def get_test():
    pass

async def post_test():
    pass

def on_routes():
    return [
        ("GET", "/test", get_test),
        ("POST", "/test", post_test),
    ]
```

## License

See the [LICENSE](./LICENSE) file for details. In summary,
**reccd** is licensed under the **MIT license**.
