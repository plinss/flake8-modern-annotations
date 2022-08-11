# [flake8-modern-annotations](https://github.com/plinss/flake8-modern-annotations)

flake8 plugin to validate type annotations accorind go tmodern practices.

* Postponed Evaluations of Annotations per PEP 563.

This plugin is used to enforce consistent usage of postponed evaluation of type annotations,
returning an error code when string literals are used for a type.

### Activation

By default the plugin activates when it sees an import that enables PEP563, e.g.:

    from __future__ import annotations

The `modern-annotations-postponed` option may be set to 'always' or 'never',
to force a specific behavior.


## Installation

Standard python package installation:

    pip install flake8-modern-annotations


## Options

`modern-annotations-postponed`
: Controls validation of postponed annotations, 
choices: `auto`, `always`, `never` (default: `auto`)

`modern-annotations-include-name`
: Include plugin name in messages

`modern-annotations-no-include-name`
: Do not include plugin name in messages (default setting)

All options may be specified on the command line with a `--` prefix,
or can be placed in your flake8 config file.


## Error Codes

| Code   | Message |
|--------|---------|
| MDA001 | Remove quotes from variable type annotation 'type'
| MDA002 | Remove quotes from argument type annotation 'type'
| MDA003 | Remove quotes from return type annotation 'type'


## Examples

```
x: 'Foo'  <-- MDA001
def foo(x: 'Foo') -> None:  <-- MDA002
def foo(x: Foo) -> 'Bar':  <-- MDA003
```