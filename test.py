#!/usr/bin/env python3
"""Unit tests."""

import os
import subprocess
import tempfile
import unittest
from typing import List


def flake8(test: str, options: List[str] = None) -> List[str]:
	"""Run flake8 on test input and return output."""
	with tempfile.NamedTemporaryFile(delete=False) as temp_file:
		temp_file.write(test.encode('utf-8'))
	# print(test)
	# print(' '.join(['flake8', '--isolated', '--select=MDA', temp_file.name] + [f'--modern-annotations-{option}' for option in (options or [])]))
	process = subprocess.Popen(['flake8', '--isolated', '--select=MDA', temp_file.name] + [f'--modern-annotations-{option}' for option in (options or [])],
	                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	os.remove(temp_file.name)
	if (stderr):
		print(stderr.decode('utf-8'))
		return [f'0:0:{line}' for line in stderr.decode('utf-8').splitlines()]
	# print(repr([line.split(':', 1)[1] for line in stdout.decode('utf-8').splitlines()]))
	return [line.split(':', 1)[1] for line in stdout.decode('utf-8').splitlines()]


class TestAnnotations(unittest.TestCase):
	"""Test annotation handling."""

	def test_valid(self) -> None:
		options = ['postponed=always']
		self.assertEqual(flake8('x: int', options), [])
		self.assertEqual(flake8('x: int = 2', options), [])
		self.assertEqual(flake8('x: Dict[str, int]', options), [])
		self.assertEqual(flake8('x: Dict[str, int] = {}', options), [])
		self.assertEqual(flake8('x: Dict[str, List[Optional[Union[str, int]]]]', options), [])
		self.assertEqual(flake8('x: Dict[str, List[Optional[Union[str, int]]]] = {}', options), [])
		self.assertEqual(flake8('def func(x: int) -> None:\n    pass', options), [])
		self.assertEqual(flake8('def func(x: int = None) -> str:\n    pass', options), [])

	def test_quoted(self) -> None:
		options = ['postponed=always']
		self.assertEqual(flake8("x: 'int'", options), [
			"1:4: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: 'int' = 2", options), [
			"1:4: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, 'int']", options), [
			"1:14: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, 'int'] = {}", options), [
			"1:14: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, List[Optional[Union[str, 'int']]]]", options), [
			"1:39: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, List[Optional[Union[str, 'int']]]] = {}", options), [
			"1:39: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("def func(x: 'int') -> None:\n    pass", options), [
			"1:13: MDA002 Remove quotes from argument type annotation 'int'",
		])
		self.assertEqual(flake8("def func(x: int = None) -> 'None':\n    pass", options), [
			"1:28: MDA003 Remove quotes from return type annotation 'None'",
		])
		self.assertEqual(flake8("def func(x: 'int' = None) -> 'None':\n    pass", options), [
			"1:13: MDA002 Remove quotes from argument type annotation 'int'",
			"1:30: MDA003 Remove quotes from return type annotation 'None'",
		])

	def test_typing_literal(self) -> None:
		options = ['postponed=always']
		self.assertEqual(flake8("import typing\ndef func() -> typing.Literal[False]:\n    pass", options), [
		])
		self.assertEqual(flake8("import typing as typ\ndef func() -> typ.Literal[False]:\n    pass", options), [
		])
		self.assertEqual(flake8("from typing import Literal\ndef func() -> Literal['False']:\n    pass", options), [
		])
		self.assertEqual(flake8("from typing import Literal as Lit\ndef func() -> Lit[False]:\n    pass", options), [
		])

	def test_typing_extensions_literal(self) -> None:
		options = ['postponed=always']
		self.assertEqual(flake8("import typing_extensions\ndef func() -> typing_extensions.Literal[False]:\n    pass", options), [
		])
		self.assertEqual(flake8("import typing_extensions as typ\ndef func() -> typ.Literal[False]:\n    pass", options), [
		])
		self.assertEqual(flake8("from typing_extensions import Literal\ndef func() -> Literal['False']:\n    pass", options), [
		])
		self.assertEqual(flake8("from typing_extensions import Literal as Lit\ndef func() -> Lit[False]:\n    pass", options), [
		])

	def test_callable(self) -> None:
		options = ['postponed=always', 'deprecated=never']
		self.assertEqual(flake8("from typing import Callable\ndef func(x: Callable[..., None]) -> None:\n    pass", options), [
		])

	def test_deprecated(self) -> None:
		options = ['deprecated=always']
		self.assertEqual(flake8("import typing\ndef func(x: typing.Dict[str, str]) -> None:\n    pass", options), [
			"2:13: MDA202 Replace 'typing.Dict' with 'dict'",
		])
		self.assertEqual(flake8("import typing as typ\ndef func(x: typ.Dict[str, str]) -> None:\n    pass", options), [
			"2:13: MDA202 Replace 'typ.Dict' with 'dict'",
		])
		self.assertEqual(flake8("from typing import Dict\ndef func(x: Dict[str, str]) -> None:\n    pass", options), [
			"1:1: MDA102 'typing.Dict' is deprecated, remove from import",
			"2:13: MDA202 Replace 'Dict' with 'dict'",
		])
		self.assertEqual(flake8("from typing import Dict as TDict\ndef func(x: TDict[str, str]) -> None:\n    pass", options), [
			"1:1: MDA102 'typing.Dict' is deprecated, remove from import",
			"2:13: MDA202 Replace 'TDict' with 'dict'",
		])
		self.assertEqual(flake8("import typing\ndef func(x: typing.Mapping[str, str]) -> typing.Mapping:\n    y: typing.Dict[str, str] = dict(x)\n    return y", options), [
			"2:13: MDA234 Replace 'typing.Mapping' with 'collections.abc.Mapping'",
			"2:42: MDA234 Replace 'typing.Mapping' with 'collections.abc.Mapping'",
			"3:8: MDA202 Replace 'typing.Dict' with 'dict'",
		])
		self.assertEqual(flake8("from typing import Dict, Mapping\ndef func(x: Mapping[str, str]) -> Mapping:\n    y: Dict[str, str] = dict(x)\n    return y", options), [
			"1:1: MDA102 'typing.Dict' is deprecated, remove from import",
			"1:1: MDA134 'typing.Mapping' is deprecated, replace with 'collections.abc.Mapping'",
			"2:13: MDA234 Replace 'Mapping' with 'collections.abc.Mapping'",
			"2:35: MDA234 Replace 'Mapping' with 'collections.abc.Mapping'",
			"3:8: MDA202 Replace 'Dict' with 'dict'",
		])
		self.assertEqual(flake8("from typing import Dict as TDict\nx: TDict[str, str] = {}", options), [
			"1:1: MDA102 'typing.Dict' is deprecated, remove from import",
			"2:4: MDA202 Replace 'TDict' with 'dict'",
		])

	def test_allowed_type_alias(self) -> None:
		options = ['deprecated=always', 'type-alias=always']
		self.assertEqual(flake8("import typing\nMyDict = typing.Dict[str, typing.List]", options), [
		])
		self.assertEqual(flake8("import typing as typ\nMyDict = typ.Dict[str, typ.List]", options), [
		])
		self.assertEqual(flake8("from typing import Dict, List\nMyDict = Dict[str, List]", options), [
		])
		self.assertEqual(flake8("from typing import Dict as TDict, List as TList\nMyDict = TDict[str, TList]", options), [
		])

	def test_required_type_alias(self) -> None:
		options = ['deprecated=always', 'type-alias=always']
		self.assertEqual(flake8("MyDict = dict[str, list]", options), [
			"1:10: MDA302 Replace 'dict' with 'typing.Dict' for type alias",
			"1:20: MDA301 Replace 'list' with 'typing.List' for type alias",
		])
		self.assertEqual(flake8("from collections.abc import Mapping, Sequence\nMyDict = Mapping[str, Sequence]", options), [
			"2:10: MDA334 Replace 'Mapping' with 'typing.Mapping' for type alias",
			"2:23: MDA336 Replace 'Sequence' with 'typing.Sequence' for type alias",
		])
		self.assertEqual(flake8("from re import Match as ReMatch, Pattern as RePattern\nMyMatch = ReMatch[RePattern]", options), [
			"2:11: MDA361 Replace 'ReMatch' with 'typing.Match' for type alias",
			"2:19: MDA360 Replace 'RePattern' with 'typing.Pattern' for type alias",
		])

	def test_no_type_alias(self) -> None:
		options = ['deprecated=always', 'type-alias=never']
		self.assertEqual(flake8("import typing\nMyDict = typing.Dict[str, typing.List]", options), [
			"2:10: MDA202 Replace 'typing.Dict' with 'dict'",
			"2:27: MDA201 Replace 'typing.List' with 'list'",
		])
		self.assertEqual(flake8("import typing as typ\nMyDict = typ.Dict[str, typ.List]", options), [
			"2:10: MDA202 Replace 'typ.Dict' with 'dict'",
			"2:24: MDA201 Replace 'typ.List' with 'list'",
		])
		self.assertEqual(flake8("from typing import Dict, List\nMyDict = Dict[str, List]", options), [
			"1:1: MDA102 'typing.Dict' is deprecated, remove from import",
			"1:1: MDA101 'typing.List' is deprecated, remove from import",
			"2:10: MDA202 Replace 'Dict' with 'dict'",
			"2:20: MDA201 Replace 'List' with 'list'",
		])
		self.assertEqual(flake8("from typing import Dict as TDict, List as TList\nMyDict = TDict[str, TList]", options), [
			"1:1: MDA102 'typing.Dict' is deprecated, remove from import",
			"1:1: MDA101 'typing.List' is deprecated, remove from import",
			"2:10: MDA202 Replace 'TDict' with 'dict'",
			"2:21: MDA201 Replace 'TList' with 'list'",
		])


class TestOptions(unittest.TestCase):
	"""Test options."""

	def test_postponed(self) -> None:
		self.assertEqual(flake8("x: 'int'", ['postponed=auto']), [])
		self.assertEqual(flake8("from __future__ import annotations\nx: 'int'", ['postponed=auto']), [
			"2:4: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: 'int'", ['postponed=always']), [
			"1:4: MDA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: 'int'", ['postponed=never']), [])
		self.assertEqual(flake8("from __future__ import annotations\nx: 'int'", ['postponed=never']), [])

	def test_include_name(self) -> None:
		self.assertEqual(flake8("from __future__ import annotations\nx: 'int'", ['include-name']), [
			"2:4: MDA001 (flake8-modern-annotations) Remove quotes from variable type annotation 'int'",
		])


if __name__ == '__main__':
	unittest.main()
