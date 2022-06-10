# [flake8-postponed-annotations](https://github.com/plinss/flake8-postponed-annotations)

flake8 plugin to validate Postponed Evaluations of Annotations per PEP 563.

This plugin is used to enforce consistent usage of postponed evaluation of type annotations,
returning an error code when string literals are used for a type.

### Activation

By default the plugin activates when it sees an import that enables PEP563, e.g.:

    from __future__ import annotations

The `postponed-annotations-activation` option may be set to 'always' or 'never',
to force a specific behavior.


## Installation

Standard python package installation:

    pip install flake8-postponed-annotations


## Options

`postponed-annotations-activation`
: Controls activation of the plugin, 
choices: `auto`, `always`, `never` (default: `auto`)

`postponed-annotations-include-name`
: Include plugin name in messages

`postponed-annotations-no-include-name`
: Do not include plugin name in messages (default setting)

All options may be specified on the command line with a `--` prefix,
or can be placed in your flake8 config file.


## Error Codes

| Code   | Message |
|--------|---------|
| PEA001 | Remove quotes from type annotation 'type'


## Examples

```
x: 'Foo' = "value"  <-- PEA001
```