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
	# print(' '.join(['flake8', '--isolated', '--select=PEA', temp_file.name] + [f'--postponed-annotations-{option}' for option in (options or [])]))
	process = subprocess.Popen(['flake8', '--isolated', '--select=PEA', temp_file.name] + [f'--postponed-annotations-{option}' for option in (options or [])],
	                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	os.remove(temp_file.name)
	if (stderr):
		return [f'0:0:{line}' for line in stderr.decode('utf-8').splitlines()]
	# print(repr([line.split(':', 1)[1] for line in stdout.decode('utf-8').splitlines()]))
	return [line.split(':', 1)[1] for line in stdout.decode('utf-8').splitlines()]


class TestAnnotations(unittest.TestCase):
	"""Test annotation handling."""

	def test_valid(self) -> None:
		options = ['activation=always']
		self.assertEqual(flake8('x: int', options), [])
		self.assertEqual(flake8('x: int = 2', options), [])
		self.assertEqual(flake8('x: Dict[str, int]', options), [])
		self.assertEqual(flake8('x: Dict[str, int] = {}', options), [])
		self.assertEqual(flake8('x: Dict[str, List[Optional[Union[str, int]]]]', options), [])
		self.assertEqual(flake8('x: Dict[str, List[Optional[Union[str, int]]]] = {}', options), [])
		self.assertEqual(flake8('def func(x: int) -> None:\n    pass', options), [])
		self.assertEqual(flake8('def func(x: int = None) -> str:\n    pass', options), [])

	def test_quoted(self) -> None:
		options = ['activation=always']
		self.assertEqual(flake8("x: 'int'", options), [
			"1:4: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: 'int' = 2", options), [
			"1:4: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, 'int']", options), [
			"1:14: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, 'int'] = {}", options), [
			"1:14: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, List[Optional[Union[str, 'int']]]]", options), [
			"1:39: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: Dict[str, List[Optional[Union[str, 'int']]]] = {}", options), [
			"1:39: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("def func(x: 'int') -> None:\n    pass", options), [
			"1:13: PEA002 Remove quotes from argument type annotation 'int'",
		])
		self.assertEqual(flake8("def func(x: int = None) -> 'None':\n    pass", options), [
			"1:28: PEA003 Remove quotes from return type annotation 'None'",
		])
		self.assertEqual(flake8("def func(x: 'int' = None) -> 'None':\n    pass", options), [
			"1:13: PEA002 Remove quotes from argument type annotation 'int'",
			"1:30: PEA003 Remove quotes from return type annotation 'None'",
		])


class TestOptions(unittest.TestCase):
	"""Test options."""

	def test_activation(self) -> None:
		self.assertEqual(flake8("x: 'int'", ['activation=auto']), [])
		self.assertEqual(flake8("from __future__ import annotations\nx: 'int'", ['activation=auto']), [
			"2:4: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: 'int'", ['activation=always']), [
			"1:4: PEA001 Remove quotes from variable type annotation 'int'",
		])
		self.assertEqual(flake8("x: 'int'", ['activation=never']), [])
		self.assertEqual(flake8("from __future__ import annotations\nx: 'int'", ['activation=never']), [])

	def test_include_name(self) -> None:
		self.assertEqual(flake8("from __future__ import annotations\nx: 'int'", ['include-name']), [
			"2:4: PEA001 (flake8-postponed-annotations) Remove quotes from variable type annotation 'int'",
		])


if __name__ == '__main__':
	unittest.main()
