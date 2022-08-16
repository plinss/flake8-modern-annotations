# [flake8-modern-annotations](https://github.com/plinss/flake8-modern-annotations)

flake8 plugin to validate type annotations accoring to modern practices.

* Postponed Evaluations of Annotations per PEP 563.
* Standard collection generics per PEP 585.
* Union types as X | Y per PEP 604.

### Activation

By default the plugin activates according to the Python version used for flake8 
or when it sees a future import that enables modern annoations, e.g.:

    from __future__ import annotations

Options exist for each feature to override the automatic activation.

## Installation

Standard python package installation:

    pip install flake8-modern-annotations


## Options

`modern-annotations-postponed`
: Controls validation of postponed annotations (PEP 563), 
choices: `auto`, `always`, `never` (default: `auto`)

`modern-annotations-deprecated`
: Controls validation of deprecated types (PEP 585), 
choices: `auto`, `always`, `never` (default: `auto`)

`modern-annotations-type-alias`
: Use deprecated types in type aliases (required for older Python < 3.9), 
choices: `auto`, `always`, `never` (default: `auto`)

`modern-annotations-union`
: Controls checks for use of typing.Union (PEP 604), 
choices: `auto`, `always`, `never` (default: `auto`)

`modern-annotations-include-name`
: Include plugin name in messages

`modern-annotations-no-include-name`
: Do not include plugin name in messages (default setting)

All options may be specified on the command line with a `--` prefix,
or can be placed in your flake8 config file.

If developing code in Python 3.9+ that is expected to run on 3.7 or 3.8,
use `modern-annotations-type-alias=always` to ensure that type aliases will work.


## Error Codes

| Code   | Message |
|--------|---------|
| MDA001 | Remove quotes from variable type annotation 'type'
| MDA002 | Remove quotes from argument type annotation 'type'
| MDA003 | Remove quotes from return type annotation 'type'
| MDA100 | 'typing.Tuple' is deprecated, remove from import
| MDA101 | 'typing.List' is deprecated, remove from import
| MDA102 | 'typing.Dict' is deprecated, remove from import
| MDA103 | 'typing.Set' is deprecated, remove from import
| MDA104 | 'typing.FrozenSet' is deprecated, remove from import
| MDA105 | 'typing.Type' is deprecated, remove from import
| MDA110 | 'typing.Deque' is deprecated, replace with 'collections.deque'
| MDA111 | 'typing.DefaultDict' is deprecated, replace with 'collections.defaultdict'
| MDA112 | 'typing.OrderedDict' is deprecated, replace with 'collections.OrderedDict'
| MDA113 | 'typing.Counter' is deprecated, replace with 'collections.Counter'
| MDA114 | 'typing.ChainMap' is deprecated, replace with 'collections.ChainMap'
| MDA120 | 'typing.Awaitable' is deprecated, replace with 'collections.abc.Awaitable'
| MDA121 | 'typing.Coroutine' is deprecated, replace with 'collections.abc.Coroutine'
| MDA122 | 'typing.AsyncIterable' is deprecated, replace with 'collections.abc.AsyncIterable'
| MDA123 | 'typing.AsyncIterator' is deprecated, replace with 'collections.abc.AsyncIterator'
| MDA124 | 'typing.AsyncGenerator' is deprecated, replace with 'collections.abc.AsyncGenerator'
| MDA125 | 'typing.Iterable' is deprecated, replace with 'collections.abc.Iterable'
| MDA126 | 'typing.Iterator' is deprecated, replace with 'collections.abc.Iterator'
| MDA127 | 'typing.Generator' is deprecated, replace with 'collections.abc.Generator'
| MDA128 | 'typing.Reversible' is deprecated, replace with 'collections.abc.Reversible'
| MDA129 | 'typing.Container' is deprecated, replace with 'collections.abc.Container'
| MDA130 | 'typing.Collection' is deprecated, replace with 'collections.abc.Collection'
| MDA131 | 'typing.Callable' is deprecated, replace with 'collections.abc.Callable'
| MDA132 | 'typing.AbstractSet' is deprecated, replace with 'collections.abc.Set'
| MDA133 | 'typing.MutableSet' is deprecated, replace with 'collections.abc.MutableSet'
| MDA134 | 'typing.Mapping' is deprecated, replace with 'collections.abc.Mapping'
| MDA135 | 'typing.MutableMapping' is deprecated, replace with 'collections.abc.MutableMapping'
| MDA136 | 'typing.Sequence' is deprecated, replace with 'collections.abc.Sequence'
| MDA137 | 'typing.MutableSequence' is deprecated, replace with 'collections.abc.MutableSequence'
| MDA138 | 'typing.ByteString' is deprecated, replace with 'collections.abc.ByteString'
| MDA139 | 'typing.MappingView' is deprecated, replace with 'collections.abc.MappingView'
| MDA140 | 'typing.KeysView' is deprecated, replace with 'collections.abc.KeysView'
| MDA141 | 'typing.ItemsView' is deprecated, replace with 'collections.abc.ItemsView'
| MDA142 | 'typing.ValuesView' is deprecated, replace with 'collections.abc.ValuesView'
| MDA150 | 'typing.ContextManager' is deprecated, replace with 'contextlib.AbstractContextManager'
| MDA151 | 'typing.AsyncContextManager' is deprecated, replace with 'contextlib.AbstractAsyncContextManager'
| MDA160 | 'typing.Pattern' is deprecated, replace with 're.Pattern'
| MDA161 | 'typing.Match' is deprecated, replace with 're.Match'
| MDA200 | Replace 'Tuple' with 'tuple'
| MDA201 | Replace 'List' with 'list'
| MDA202 | Replace 'Dict' with 'dict'
| MDA203 | Replace 'Set' with 'set'
| MDA204 | Replace 'FrozenSet' with 'frozenset'
| MDA205 | Replace 'Type' with 'type'
| MDA210 | Replace 'Deque' with 'collections.deque'
| MDA211 | Replace 'DefaultDict' with 'collections.defaultdict'
| MDA212 | Replace 'OrderedDict' with 'collections.OrderedDict'
| MDA213 | Replace 'Counter' with 'collections.Counter'
| MDA214 | Replace 'ChainMap' with 'collections.ChainMap'
| MDA220 | Replace 'Awaitable' with 'collections.abc.Awaitable'
| MDA221 | Replace 'Coroutine' with 'collections.abc.Coroutine'
| MDA222 | Replace 'AsyncIterable' with 'collections.abc.AsyncIterable'
| MDA223 | Replace 'AsyncIterator' with 'collections.abc.AsyncIterator'
| MDA224 | Replace 'AsyncGenerator' with 'collections.abc.AsyncGenerator'
| MDA225 | Replace 'Iterable' with 'collections.abc.Iterable'
| MDA226 | Replace 'Iterator' with 'collections.abc.Iterator'
| MDA227 | Replace 'Generator' with 'collections.abc.Generator'
| MDA228 | Replace 'Reversible' with 'collections.abc.Reversible'
| MDA229 | Replace 'Container' with 'collections.abc.Container'
| MDA230 | Replace 'Collection' with 'collections.abc.Collection'
| MDA231 | Replace 'Callable' with 'collections.abc.Callable'
| MDA232 | Replace 'AbstractSet' with 'collections.abc.Set'
| MDA233 | Replace 'MutableSet' with 'collections.abc.MutableSet'
| MDA234 | Replace 'Mapping' with 'collections.abc.Mapping'
| MDA235 | Replace 'MutableMapping' with 'collections.abc.MutableMapping'
| MDA236 | Replace 'Sequence' with 'collections.abc.Sequence'
| MDA237 | Replace 'MutableSequence' with 'collections.abc.MutableSequence'
| MDA238 | Replace 'ByteString' with 'collections.abc.ByteString'
| MDA239 | Replace 'MappingView' with 'collections.abc.MappingView'
| MDA240 | Replace 'KeysView' with 'collections.abc.KeysView'
| MDA241 | Replace 'ItemsView' with 'collections.abc.ItemsView'
| MDA242 | Replace 'ValuesView' with 'collections.abc.ValuesView'
| MDA250 | Replace 'ContextManager' with 'contextlib.AbstractContextManager'
| MDA251 | Replace 'AsyncContextManager' with 'contextlib.AbstractAsyncContextManager'
| MDA260 | Replace 'Pattern' with 're.Pattern'
| MDA261 | Replace 'Match' with 're.Match'
| MDA400 | 'typing.Union' is deprecated, remove from import
| MDA401 | Replace 'Union' with |


## Examples

```
x: 'Foo'  <-- MDA001
def foo(x: 'Foo') -> None:  <-- MDA002
def foo(x: Foo) -> 'Bar':  <-- MDA003

from typing import Dict  <-- MDA102
x: Dict[str, str]  <-- MDA202

from typing import Dict
MyDict = Dict[str, int]  <-- no error on Python 3.7/3.8

from typing import Union  <-- MDA400
x: Union[int, float]  <-- MDA401
```