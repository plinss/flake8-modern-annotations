"""Checker for string literals in type annotations."""

from __future__ import annotations

import ast
import enum
import sys
import tokenize
from typing import ClassVar, Iterator, Tuple, Type, cast

from flake8.options.manager import OptionManager

import flake8_postponed_annotations

from typing_extensions import Protocol


try:
	import pkg_resources
	package_version = pkg_resources.get_distribution(__package__).version
except pkg_resources.DistributionNotFound:
	package_version = 'unknown'


class Options(Protocol):
	"""Protocol for options."""

	postponed_annotations_activation: str
	postponed_annotations_include_name: bool


LogicalResult = Tuple[Tuple[int, int], str]  # (line, column), text
PhysicalResult = Tuple[int, str]  # (column, text)
ASTResult = Tuple[int, int, str, Type]  # (line, column, text, Type)


class Message(enum.Enum):
	"""Messages."""

	UNQUOTE_TYPE = (1, "Remove quotes from type annotation '{value}'")

	@property
	def code(self) -> str:
		return (flake8_postponed_annotations.plugin_prefix + str(self.value[0]).rjust(6 - len(flake8_postponed_annotations.plugin_prefix), '0'))

	def text(self, **kwargs) -> str:
		return self.value[1].format(**kwargs)


class Checker:
	"""Base class for checkers."""

	name: ClassVar[str] = __package__.replace('_', '-')
	version: ClassVar[str] = package_version
	plugin_name: ClassVar[str]
	activation: ClassVar[str] = 'auto'

	@classmethod
	def add_options(cls, option_manager: OptionManager) -> None:
		option_manager.add_option('--postponed-annotations-activation', default='auto',
		                          action='store', parse_from_config=True,
		                          choices=('auto', 'always', 'never'), dest='postponed_annotations_activation',
		                          help="Activate plugin, auto checks for 'from __future__ import annotations' (default: auto)")
		option_manager.add_option('--postponed-annotations-include-name', default=False, action='store_true',
		                          parse_from_config=True, dest='postponed_annotations_include_name',
		                          help='Include plugin name in messages (enabled by default)')
		option_manager.add_option('--postponed-annotations-no-include-name', default=None, action='store_false',
		                          parse_from_config=False, dest='postponed_annotations_include_name',
		                          help='Remove plugin name from messages')

	@classmethod
	def parse_options(cls, options: Options) -> None:
		cls.plugin_name = (' (' + cls.name + ')') if (options.postponed_annotations_include_name) else ''
		if ((sys.version_info.major == 3) and (sys.version_info.minor < 7)):
			cls.activation = 'never'
		else:
			cls.activation = options.postponed_annotations_activation

	def _logical_token_message(self, token: tokenize.TokenInfo, message: Message, **kwargs) -> LogicalResult:
		return (token.start, f'{message.code}{self.plugin_name} {message.text(**kwargs)}')

	def _pyhsical_token_message(self, token: tokenize.TokenInfo, message: Message, **kwargs) -> PhysicalResult:
		return (token.start[1], f'{message.code}{self.plugin_name} {message.text(**kwargs)}')

	def _ast_token_message(self, token: tokenize.TokenInfo, message: Message, **kwargs) -> ASTResult:
		return (token.start[0], token.start[1], f'{message.code}{self.plugin_name} {message.text(**kwargs)}', type(self))

	def _ast_node_message(self, node: ast.AST, message: Message, **kwargs) -> ASTResult:
		return (node.lineno, node.col_offset, f'{message.code}{self.plugin_name} {message.text(**kwargs)}', type(self))


class AnnotationChecker(Checker):
	"""Annotation checker."""

	tree: ast.AST
	enabled: bool

	def __init__(self, tree: ast.AST) -> None:
		self.tree = tree
		self.enabled = ('always' == self.activation)

	def _check_annotation(self, annotation: ast.AST) -> Iterator[ASTResult]:
		if (isinstance(annotation, ast.Constant)):
			if (annotation.value is None):
				return
			yield self._ast_node_message(annotation, Message.UNQUOTE_TYPE, value=annotation.value)
		elif (isinstance(annotation, ast.Subscript)):
			value = annotation.slice.value if (isinstance(annotation.slice, ast.Index)) else annotation.slice

			if (isinstance(value, ast.Tuple)):
				for item in value.elts:
					for result in self._check_annotation(item):
						yield result
			else:
				for result in self._check_annotation(value):
					yield result
		else:
			try:
				if (isinstance(annotation, ast.Str)):  # python3.7
					if (annotation.s is None):
						return
					yield self._ast_node_message(annotation, Message.UNQUOTE_TYPE, value=annotation.s)
			except AttributeError:
				pass

	def __iter__(self) -> Iterator[ASTResult]:
		"""Primary call from flake8, yield error messages."""
		if ((not self.enabled) and ('never' != self.activation)):

			class ImportVisitor(ast.NodeVisitor):
				def __init__(self) -> None:
					self.enabled = False

				def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
					if (self.enabled or ('__future__' != node.module)):
						return

					for alias in node.names:
						if ('annotations' == alias.name):
							self.enabled = True
							return

			enable_visitor = ImportVisitor()
			enable_visitor.visit(self.tree)
			self.enabled = enable_visitor.enabled

		if (not self.enabled):
			return

		for node in ast.walk(self.tree):
			if (hasattr(node, 'annotation')):
				annotation = cast(ast.arg, node).annotation
			elif (isinstance(node, ast.FunctionDef)):
				annotation = node.returns
			else:
				continue

			for result in self._check_annotation(cast(ast.AST, annotation)):
				yield result
