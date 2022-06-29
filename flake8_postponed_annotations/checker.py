"""Checker for string literals in type annotations."""

from __future__ import annotations

import ast
import enum
import sys
from typing import ClassVar, Iterator, List, Optional, TYPE_CHECKING, Tuple, Type

import flake8_postponed_annotations

from typing_extensions import Protocol

if (TYPE_CHECKING):
	import tokenize
	from flake8.options.manager import OptionManager


try:
	try:
		from importlib.metadata import version
	except ModuleNotFoundError:  # python < 3.8 use polyfill
		from importlib_metadata import version  # type: ignore
	package_version = version(__package__)
except Exception:
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

	ASSIGN_TYPE = (1, "Remove quotes from variable type annotation '{value}'")
	ARG_TYPE = (2, "Remove quotes from argument type annotation '{value}'")
	RETURN_TYPE = (3, "Remove quotes from return type annotation '{value}'")

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


class ImportVisitor(ast.NodeVisitor):
	"""Import visitor."""

	enabled: bool

	def __init__(self) -> None:
		self.enabled = False

	def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
		if (self.enabled or ('__future__' != node.module)):
			return

		for alias in node.names:
			if ('annotations' == alias.name):
				self.enabled = True
				return


class AnnotationVisitor(ast.NodeVisitor):
	"""Annotation visitor."""

	results: List[Tuple[ast.AST, Message, str]]

	def __init__(self) -> None:
		self.results = []

	def _check_annotation(self, annotation: Optional[ast.AST], message: Message) -> Iterator[Tuple[ast.AST, Message, str]]:
		if (isinstance(annotation, ast.Constant)):
			if (annotation.value is None):
				return
			yield (annotation, message, annotation.value)
		elif (isinstance(annotation, ast.Subscript)):
			value = annotation.slice.value if (isinstance(annotation.slice, ast.Index)) else annotation.slice

			if (isinstance(value, ast.Tuple)):
				for item in value.elts:
					yield from self._check_annotation(item, message)
			else:
				yield from self._check_annotation(value, message)
		else:
			try:
				if (isinstance(annotation, ast.Str)):  # python3.7
					if (annotation.s is None):
						return
					yield (annotation, message, annotation.s)
			except AttributeError:
				pass

	def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
		self.results.extend(self._check_annotation(node.annotation, Message.ASSIGN_TYPE))

	def visit_arg(self, node: ast.arg) -> None:
		self.results.extend(self._check_annotation(node.annotation, Message.ARG_TYPE))

	def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
		self.generic_visit(node)
		self.results.extend(self._check_annotation(node.returns, Message.RETURN_TYPE))


class AnnotationChecker(Checker):
	"""Annotation checker."""

	tree: ast.AST
	enabled: bool

	def __init__(self, tree: ast.AST) -> None:
		self.tree = tree
		self.enabled = ('always' == self.activation)

	def __iter__(self) -> Iterator[ASTResult]:
		"""Primary call from flake8, yield error messages."""
		if ((not self.enabled) and ('never' != self.activation)):
			import_visitor = ImportVisitor()
			import_visitor.visit(self.tree)
			self.enabled = import_visitor.enabled

		if (not self.enabled):
			return

		annotation_visitor = AnnotationVisitor()
		annotation_visitor.visit(self.tree)

		for node, message, value in annotation_visitor.results:
			yield self._ast_node_message(node, message, value=value)
