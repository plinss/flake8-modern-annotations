"""Checker for string literals in type annotations."""

from __future__ import annotations

import ast
import enum
import sys
from typing import ClassVar, Optional, TYPE_CHECKING, Tuple, Type

import flake8_modern_annotations

from typing_extensions import Protocol

if (TYPE_CHECKING):
	import tokenize
	from collections.abc import Iterator, Mapping
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

	modern_annotations_postponed: str
	modern_annotations_include_name: bool


LogicalResult = Tuple[Tuple[int, int], str]  # (line, column), text
PhysicalResult = Tuple[int, str]  # (column, text)
ASTResult = Tuple[int, int, str, Type]  # (line, column, text, Type)


class Message(enum.Enum):
	"""Messages."""

	POSTPONED_ASSIGN_TYPE = (1, "Remove quotes from variable type annotation '{value}'")
	POSTPONED_ARG_TYPE = (2, "Remove quotes from argument type annotation '{value}'")
	POSTPONED_RETURN_TYPE = (3, "Remove quotes from return type annotation '{value}'")

	@property
	def code(self) -> str:
		return (flake8_modern_annotations.plugin_prefix + str(self.value[0]).rjust(6 - len(flake8_modern_annotations.plugin_prefix), '0'))

	def text(self, **kwargs) -> str:
		return self.value[1].format(**kwargs)


class Checker:
	"""Base class for checkers."""

	name: ClassVar[str] = __package__.replace('_', '-')
	version: ClassVar[str] = package_version
	plugin_name: ClassVar[str]
	postponed_option: ClassVar[str] = 'auto'

	@classmethod
	def add_options(cls, option_manager: OptionManager) -> None:
		option_manager.add_option('--modern-annotations-postponed', default='auto',
		                          action='store', parse_from_config=True,
		                          choices=('auto', 'always', 'never'), dest='modern_annotations_postponed',
		                          help="Activate plugin, auto checks for 'from __future__ import annotations' (default: auto)")
		option_manager.add_option('--modern-annotations-include-name', default=False, action='store_true',
		                          parse_from_config=True, dest='modern_annotations_include_name',
		                          help='Include plugin name in messages (enabled by default)')
		option_manager.add_option('--modern-annotations-no-include-name', default=None, action='store_false',
		                          parse_from_config=False, dest='modern_annotations_include_name',
		                          help='Remove plugin name from messages')

	@classmethod
	def parse_options(cls, options: Options) -> None:
		cls.plugin_name = (' (' + cls.name + ')') if (options.modern_annotations_include_name) else ''
		if ((sys.version_info.major == 3) and (sys.version_info.minor < 7)):
			cls.postponed_option = 'never'
		else:
			cls.postponed_option = options.modern_annotations_postponed

	def _logical_token_message(self, token: tokenize.TokenInfo, message: Message, **kwargs) -> LogicalResult:
		return (token.start, f'{message.code}{self.plugin_name} {message.text(**kwargs)}')

	def _pyhsical_token_message(self, token: tokenize.TokenInfo, message: Message, **kwargs) -> PhysicalResult:
		return (token.start[1], f'{message.code}{self.plugin_name} {message.text(**kwargs)}')

	def _ast_token_message(self, token: tokenize.TokenInfo, message: Message, **kwargs) -> ASTResult:
		return (token.start[0], token.start[1], f'{message.code}{self.plugin_name} {message.text(**kwargs)}', type(self))

	def _ast_node_message(self, node: ast.AST, message: Message, **kwargs) -> ASTResult:
		return (node.lineno, node.col_offset, f'{message.code}{self.plugin_name} {message.text(**kwargs)}', type(self))


class FutureVisitor(ast.NodeVisitor):
	"""Future import visitor."""

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


TYPING_TYPES = {
	'Tuple',
	'List',
	'Dict',
	'Set',
	'FrozenSet',
	'Type',
	'Deque',
	'DefaultDict',
	'OrderedDict',
	'Counter',
	'ChainMap',
	'Awaitable',
	'Coroutine',
	'AsyncIterable',
	'AsyncIterator',
	'AsyncGenerator',
	'Iterable',
	'Iterator',
	'Generator',
	'Reversible',
	'Container',
	'Collection',
	'Callable',
	'AbstractSet',
	'MutableSet',
	'Mapping',
	'MutableMapping',
	'Sequence',
	'MutableSequence',
	'ByteString',
	'MappingView',
	'KeysView',
	'ItemsView',
	'ValuesView',
	'ContextManager',
	'AsyncContextManager',
	'Pattern',
	'Match',
	'Literal',
}


class ImportVisitor(ast.NodeVisitor):
	"""Import visitor."""

	type_map: dict[str, str]

	def __init__(self) -> None:
		self.type_map = {}

	def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
		for alias in node.names:
			if ('typing' == alias.name):
				import_name = (alias.asname or alias.name)
				for type_name in TYPING_TYPES:
					self.type_map[f'{import_name}.{type_name}'] = type_name
			elif ('typing_extensions' == alias.name):
				import_name = (alias.asname or alias.name)
				self.type_map[f'{import_name}.Literal'] = 'Literal'

	def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
		if ('typing' == node.module):
			for alias in node.names:
				self.type_map[alias.asname or alias.name] = alias.name
		elif ('typing_extensions' == node.module):
			for alias in node.names:
				if ('Literal' == alias.name):
					self.type_map[alias.asname or alias.name] = alias.name


class PostponedAnnotationVisitor(ast.NodeVisitor):
	"""Postponed annotation visitor."""

	type_map: Mapping[str, str]
	results: list[tuple[ast.AST, Message, str]]

	def __init__(self, type_map: Mapping[str, str]) -> None:
		self.type_map = type_map
		self.results = []

	def _check_annotation(self, annotation: Optional[ast.AST], message: Message) -> Iterator[tuple[ast.AST, Message, str]]:
		if (isinstance(annotation, ast.Constant)):
			if ((annotation.value is None) or isinstance(annotation.value, type(Ellipsis))):
				return
			yield (annotation, message, annotation.value)
		elif (isinstance(annotation, ast.Subscript)):
			# skip Literal[]
			if (isinstance(annotation.value, ast.Name)):
				if ('Literal' == self.type_map.get(annotation.value.id)):
					return
			if (isinstance(annotation.value, ast.Attribute) and isinstance(annotation.value.value, ast.Name)):
				attribute = annotation.value
				type_name = f'{attribute.value.id}.{attribute.attr}'  # type: ignore
				if ('Literal' == self.type_map.get(type_name)):
					return

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
		self.results.extend(self._check_annotation(node.annotation, Message.POSTPONED_ASSIGN_TYPE))

	def visit_arg(self, node: ast.arg) -> None:
		self.results.extend(self._check_annotation(node.annotation, Message.POSTPONED_ARG_TYPE))

	def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
		self.generic_visit(node)
		self.results.extend(self._check_annotation(node.returns, Message.POSTPONED_RETURN_TYPE))


class AnnotationChecker(Checker):
	"""Annotation checker."""

	tree: ast.AST
	postponed: bool

	def __init__(self, tree: ast.AST) -> None:
		self.tree = tree
		self.postponed = ('always' == self.postponed_option)

	def __iter__(self) -> Iterator[ASTResult]:
		"""Primary call from flake8, yield error messages."""
		if ((not self.postponed) and ('never' != self.postponed_option)):
			future_visitor = FutureVisitor()
			future_visitor.visit(self.tree)
			self.postponed = future_visitor.enabled

		if (not (self.postponed)):
			return

		import_visitor = ImportVisitor()
		import_visitor.visit(self.tree)

		if (self.postponed):
			postponed_visitor = PostponedAnnotationVisitor(import_visitor.type_map)
			postponed_visitor.visit(self.tree)

			for node, message, value in postponed_visitor.results:
				yield self._ast_node_message(node, message, value=value)
