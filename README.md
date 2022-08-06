# reccd

![PyPI](https://img.shields.io/pypi/v/reccd?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/reccd?style=flat-square)
![GitHub](https://img.shields.io/github/license/bogonets/reccd?style=flat-square)

Daemon helper for the ANSWER

## About

A wrapper to easily adapt gRPC communication without implementing protobuf.

## Usage

Print help message:
```.shell
python -m reccd --help
```

Print version number:
```.shell
python -m reccd --version
```

Prints a list of available modules:
```.shell
python -m reccd -vvv modules
```

Start the gRPC daemon server:
```.shell
python -m reccd -l -d -vvv server -a 0.0.0.0:8080 template
```

Communicates with the daemon server:
```.shell
python -m reccd -l -d -vvv client -a 0.0.0.0:8080 message
```

## License

See the [LICENSE](./LICENSE) file for details. In summary,
**reccd** is licensed under the **MIT license**.
