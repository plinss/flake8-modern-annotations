"""Checker for string literals in type annotations."""

from __future__ import annotations

import ast
import enum
import sys
from typing import ClassVar, Dict, Optional, TYPE_CHECKING, Tuple, Type

import flake8_modern_annotations

from typing_extensions import Protocol

if (TYPE_CHECKING):
	import tokenize
	from collections.abc import Iterator
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
	modern_annotations_deprecated: str
	modern_annotations_type_alias: str
	modern_annotations_union: str
	modern_annotations_union_paren: str
	modern_annotations_include_name: bool


LogicalResult = Tuple[Tuple[int, int], str]  # (line, column), text
PhysicalResult = Tuple[int, str]  # (column, text)
ASTResult = Tuple[int, int, str, Type]  # (line, column, text, Type)


REMOVE_IMPORT = "'{name}' is deprecated, remove from import"
REPLACE_IMPORT = "'{name}' is deprecated, replace with '{replacement}'"
REPLACE_TYPE = "Replace '{name}' with '{replacement}'"
REQUIRE_TYPE = "Replace '{name}' with '{replacement}' for type alias"


class Message(enum.Enum):
	"""Messages."""

	POSTPONED_ASSIGN_TYPE = (1, "Remove quotes from variable type annotation '{value}'")
	POSTPONED_ARG_TYPE = (2, "Remove quotes from argument type annotation '{value}'")
	POSTPONED_RETURN_TYPE = (3, "Remove quotes from return type annotation '{value}'")

	DEPRECATED_IMPORT_TUPLE = (100, REMOVE_IMPORT)
	DEPRECATED_IMPORT_LIST = (101, REMOVE_IMPORT)
	DEPRECATED_IMPORT_DICT = (102, REMOVE_IMPORT)
	DEPRECATED_IMPORT_SET = (103, REMOVE_IMPORT)
	DEPRECATED_IMPORT_FROZEN_SET = (104, REMOVE_IMPORT)
	DEPRECATED_IMPORT_TYPE = (105, REMOVE_IMPORT)

	REPLACED_IMPORT_DEQUE = (110, REPLACE_IMPORT)
	REPLACED_IMPORT_DEFAULT_DICT = (111, REPLACE_IMPORT)
	REPLACED_IMPORT_ORDERED_DICT = (112, REPLACE_IMPORT)
	REPLACED_IMPORT_COUNTER = (113, REPLACE_IMPORT)
	REPLACED_IMPORT_CHAIN_MAP = (114, REPLACE_IMPORT)
	REPLACED_IMPORT_AWAITABLE = (120, REPLACE_IMPORT)
	REPLACED_IMPORT_COROUTINE = (121, REPLACE_IMPORT)
	REPLACED_IMPORT_ASYNC_ITERABLE = (122, REPLACE_IMPORT)
	REPLACED_IMPORT_ASYNC_ITERATOR = (123, REPLACE_IMPORT)
	REPLACED_IMPORT_ASYNC_GENERATOR = (124, REPLACE_IMPORT)
	REPLACED_IMPORT_ITERABLE = (125, REPLACE_IMPORT)
	REPLACED_IMPORT_ITERATOR = (126, REPLACE_IMPORT)
	REPLACED_IMPORT_GENERATOR = (127, REPLACE_IMPORT)
	REPLACED_IMPORT_REVERSIBLE = (128, REPLACE_IMPORT)
	REPLACED_IMPORT_CONTAINER = (129, REPLACE_IMPORT)
	REPLACED_IMPORT_COLLECTION = (130, REPLACE_IMPORT)
	REPLACED_IMPORT_CALLABLE = (131, REPLACE_IMPORT)
	REPLACED_IMPORT_ABSTRACT_SET = (132, REPLACE_IMPORT)
	REPLACED_IMPORT_MUTABLE_SET = (133, REPLACE_IMPORT)
	REPLACED_IMPORT_MAPPING = (134, REPLACE_IMPORT)
	REPLACED_IMPORT_MUTABLE_MAPPING = (135, REPLACE_IMPORT)
	REPLACED_IMPORT_SEQUENCE = (136, REPLACE_IMPORT)
	REPLACED_IMPORT_MUTABLE_SEQUENCE = (137, REPLACE_IMPORT)
	REPLACED_IMPORT_BYTE_STRING = (138, REPLACE_IMPORT)
	REPLACED_IMPORT_MAPPING_VIEW = (139, REPLACE_IMPORT)
	REPLACED_IMPORT_KEYS_VIEW = (140, REPLACE_IMPORT)
	REPLACED_IMPORT_ITEMS_VIEW = (141, REPLACE_IMPORT)
	REPLACED_IMPORT_VALUES_VIEW = (142, REPLACE_IMPORT)
	REPLACED_IMPORT_CONTEXT_MANAGER = (150, REPLACE_IMPORT)
	REPLACED_IMPORT_ASYNC_CONTEXT_MANAGER = (151, REPLACE_IMPORT)
	REPLACED_IMPORT_PATTERN = (160, REPLACE_IMPORT)
	REPLACED_IMPORT_MATCH = (161, REPLACE_IMPORT)

	DEPRECATED_TYPE_TUPLE = (200, REPLACE_TYPE)
	DEPRECATED_TYPE_LIST = (201, REPLACE_TYPE)
	DEPRECATED_TYPE_DICT = (202, REPLACE_TYPE)
	DEPRECATED_TYPE_SET = (203, REPLACE_TYPE)
	DEPRECATED_TYPE_FROZEN_SET = (204, REPLACE_TYPE)
	DEPRECATED_TYPE_TYPE = (205, REPLACE_TYPE)
	DEPRECATED_TYPE_DEQUE = (210, REPLACE_TYPE)
	DEPRECATED_TYPE_DEFAULT_DICT = (211, REPLACE_TYPE)
	DEPRECATED_TYPE_ORDERED_DICT = (212, REPLACE_TYPE)
	DEPRECATED_TYPE_COUNTER = (213, REPLACE_TYPE)
	DEPRECATED_TYPE_CHAIN_MAP = (214, REPLACE_TYPE)
	DEPRECATED_TYPE_AWAITABLE = (220, REPLACE_TYPE)
	DEPRECATED_TYPE_COROUTINE = (221, REPLACE_TYPE)
	DEPRECATED_TYPE_ASYNC_ITERABLE = (222, REPLACE_TYPE)
	DEPRECATED_TYPE_ASYNC_ITERATOR = (223, REPLACE_TYPE)
	DEPRECATED_TYPE_ASYNC_GENERATOR = (224, REPLACE_TYPE)
	DEPRECATED_TYPE_ITERABLE = (225, REPLACE_TYPE)
	DEPRECATED_TYPE_ITERATOR = (226, REPLACE_TYPE)
	DEPRECATED_TYPE_GENERATOR = (227, REPLACE_TYPE)
	DEPRECATED_TYPE_REVERSIBLE = (228, REPLACE_TYPE)
	DEPRECATED_TYPE_CONTAINER = (229, REPLACE_TYPE)
	DEPRECATED_TYPE_COLLECTION = (230, REPLACE_TYPE)
	DEPRECATED_TYPE_CALLABLE = (231, REPLACE_TYPE)
	DEPRECATED_TYPE_ABSTRACT_SET = (232, REPLACE_TYPE)
	DEPRECATED_TYPE_MUTABLE_SET = (233, REPLACE_TYPE)
	DEPRECATED_TYPE_MAPPING = (234, REPLACE_TYPE)
	DEPRECATED_TYPE_MUTABLE_MAPPING = (235, REPLACE_TYPE)
	DEPRECATED_TYPE_SEQUENCE = (236, REPLACE_TYPE)
	DEPRECATED_TYPE_MUTABLE_SEQUENCE = (237, REPLACE_TYPE)
	DEPRECATED_TYPE_BYTE_STRING = (238, REPLACE_TYPE)
	DEPRECATED_TYPE_MAPPING_VIEW = (239, REPLACE_TYPE)
	DEPRECATED_TYPE_KEYS_VIEW = (240, REPLACE_TYPE)
	DEPRECATED_TYPE_ITEMS_VIEW = (241, REPLACE_TYPE)
	DEPRECATED_TYPE_VALUES_VIEW = (242, REPLACE_TYPE)
	DEPRECATED_TYPE_CONTEXT_MANAGER = (250, REPLACE_TYPE)
	DEPRECATED_TYPE_ASYNC_CONTEXT_MANAGER = (251, REPLACE_TYPE)
	DEPRECATED_TYPE_PATTERN = (260, REPLACE_TYPE)
	DEPRECATED_TYPE_MATCH = (261, REPLACE_TYPE)

	REQUIRED_TYPE_TUPLE = (300, REQUIRE_TYPE)
	REQUIRED_TYPE_LIST = (301, REQUIRE_TYPE)
	REQUIRED_TYPE_DICT = (302, REQUIRE_TYPE)
	REQUIRED_TYPE_SET = (303, REQUIRE_TYPE)
	REQUIRED_TYPE_FROZEN_SET = (304, REQUIRE_TYPE)
	REQUIRED_TYPE_TYPE = (305, REQUIRE_TYPE)
	REQUIRED_TYPE_DEQUE = (310, REQUIRE_TYPE)
	REQUIRED_TYPE_DEFAULT_DICT = (311, REQUIRE_TYPE)
	REQUIRED_TYPE_ORDERED_DICT = (312, REQUIRE_TYPE)
	REQUIRED_TYPE_COUNTER = (313, REQUIRE_TYPE)
	REQUIRED_TYPE_CHAIN_MAP = (314, REQUIRE_TYPE)
	REQUIRED_TYPE_AWAITABLE = (320, REQUIRE_TYPE)
	REQUIRED_TYPE_COROUTINE = (321, REQUIRE_TYPE)
	REQUIRED_TYPE_ASYNC_ITERABLE = (322, REQUIRE_TYPE)
	REQUIRED_TYPE_ASYNC_ITERATOR = (323, REQUIRE_TYPE)
	REQUIRED_TYPE_ASYNC_GENERATOR = (324, REQUIRE_TYPE)
	REQUIRED_TYPE_ITERABLE = (325, REQUIRE_TYPE)
	REQUIRED_TYPE_ITERATOR = (326, REQUIRE_TYPE)
	REQUIRED_TYPE_GENERATOR = (327, REQUIRE_TYPE)
	REQUIRED_TYPE_REVERSIBLE = (328, REQUIRE_TYPE)
	REQUIRED_TYPE_CONTAINER = (329, REQUIRE_TYPE)
	REQUIRED_TYPE_COLLECTION = (330, REQUIRE_TYPE)
	REQUIRED_TYPE_CALLABLE = (331, REQUIRE_TYPE)
	REQUIRED_TYPE_ABSTRACT_SET = (332, REQUIRE_TYPE)
	REQUIRED_TYPE_MUTABLE_SET = (333, REQUIRE_TYPE)
	REQUIRED_TYPE_MAPPING = (334, REQUIRE_TYPE)
	REQUIRED_TYPE_MUTABLE_MAPPING = (335, REQUIRE_TYPE)
	REQUIRED_TYPE_SEQUENCE = (336, REQUIRE_TYPE)
	REQUIRED_TYPE_MUTABLE_SEQUENCE = (337, REQUIRE_TYPE)
	REQUIRED_TYPE_BYTE_STRING = (338, REQUIRE_TYPE)
	REQUIRED_TYPE_MAPPING_VIEW = (339, REQUIRE_TYPE)
	REQUIRED_TYPE_KEYS_VIEW = (340, REQUIRE_TYPE)
	REQUIRED_TYPE_ITEMS_VIEW = (341, REQUIRE_TYPE)
	REQUIRED_TYPE_VALUES_VIEW = (342, REQUIRE_TYPE)
	REQUIRED_TYPE_CONTEXT_MANAGER = (350, REQUIRE_TYPE)
	REQUIRED_TYPE_ASYNC_CONTEXT_MANAGER = (351, REQUIRE_TYPE)
	REQUIRED_TYPE_PATTERN = (360, REQUIRE_TYPE)
	REQUIRED_TYPE_MATCH = (361, REQUIRE_TYPE)

	UNION_IMPORT = (400, REMOVE_IMPORT)
	UNION_TYPE = (401, "Replace '{name}' with |")

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
	deprecated_option: ClassVar[str] = 'auto'
	type_alias_option: ClassVar[str] = 'auto'
	union_option: ClassVar[str] = 'auto'
	union_paren_option: ClassVar[str] = 'bare'

	@classmethod
	def add_options(cls, option_manager: OptionManager) -> None:
		option_manager.add_option('--modern-annotations-postponed', default='auto',
		                          action='store', parse_from_config=True,
		                          choices=('auto', 'always', 'never'), dest='modern_annotations_postponed',
		                          help="Check for literal postponed annotations, auto checks for 'from __future__ import annotations' (default: auto)")
		option_manager.add_option('--modern-annotations-deprecated', default='auto',
		                          action='store', parse_from_config=True,
		                          choices=('auto', 'always', 'never'), dest='modern_annotations_deprecated',
		                          help='Check for deprecated typing types, auto checks in Python >= 3.9 or when using future annotations (default: auto)')
		option_manager.add_option('--modern-annotations-type-alias', default='auto',
		                          action='store', parse_from_config=True,
		                          choices=('auto', 'always', 'never'), dest='modern_annotations_type_alias',
		                          help='Allow deprecated typing types in type aliases, auto allows in Python < 3.9 (default: auto)')
		option_manager.add_option('--modern-annotations-union', default='auto',
		                          action='store', parse_from_config=True,
		                          choices=('auto', 'always', 'never'), dest='modern_annotations_union',
		                          help="Check for Union type, auto checks for 'from __future__ import annotations' (default: auto)")
		option_manager.add_option('--modern-annotations-union-paren', default='auto',
		                          action='store', parse_from_config=True,
		                          choices=('bare', 'always', 'never'), dest='modern_annotations_union_paren',
		                          help="Use ()'s for | unions, bare requires when not in [] (default: bare)")

		option_manager.add_option('--modern-annotations-include-name', default=False, action='store_true',
		                          parse_from_config=True, dest='modern_annotations_include_name',
		                          help='Include plugin name in messages (enabled by default)')
		option_manager.add_option('--modern-annotations-no-include-name', default=None, action='store_false',
		                          parse_from_config=False, dest='modern_annotations_include_name',
		                          help='Remove plugin name from messages')

	@classmethod
	def parse_options(cls, options: Options) -> None:
		cls.plugin_name = (' (' + cls.name + ')') if (options.modern_annotations_include_name) else ''
		if (sys.version_info < (3, 7)):
			cls.postponed_option = 'never'
			cls.deprecated_option = 'never'
			cls.type_alias_option = 'never'
			cls.union_option = 'never'
			cls.union_paren_option = 'never'
		else:
			cls.postponed_option = options.modern_annotations_postponed
			cls.deprecated_option = options.modern_annotations_deprecated
			cls.type_alias_option = options.modern_annotations_type_alias
			cls.union_option = options.modern_annotations_union
			cls.union_paren_option = options.modern_annotations_union_paren

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
	'AbstractSet',
	'AsyncContextManager',
	'AsyncGenerator',
	'AsyncIterable',
	'AsyncIterator',
	'Awaitable',
	'ByteString',
	'Callable',
	'ChainMap',
	'Collection',
	'Container',
	'ContextManager',
	'Coroutine',
	'Counter',
	'DefaultDict',
	'Deque',
	'Dict',
	'FrozenSet',
	'Generator',
	'ItemsView',
	'Iterable',
	'Iterator',
	'KeysView',
	'List',
	'Literal',
	'LiteralString',
	'Mapping',
	'MappingView',
	'Match',
	'MutableMapping',
	'MutableSequence',
	'MutableSet',
	'OrderedDict',
	'Pattern',
	'Reversible',
	'Sequence',
	'Set',
	'Tuple',
	'Type',
	'Union',
	'ValuesView',
}

TYPING_EXTENSION_TYPES = {
	'Literal',
	'LiteralString',
	'TypeAlias',
}

COLLECTIONS_TYPES = {
	'deque',
	'defaultdict',
	'OrderedDict',
	'Counter',
	'ChainMap',
}

COLLECTIONS_ABC_TYPES = {
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
	'Set',
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
}

CONTEXTLIB_TYPES = {
	'AbstractContextManager',
	'AbstractAsyncContextManager',
}

RE_TYPES = {
	'Pattern',
	'Match',
}

LITERALS = {
	'typing.Literal',
	'typing_extensions.Literal',
}

DEPRECATED_TYPES = {
	'typing.Tuple': ('tuple', Message.DEPRECATED_IMPORT_TUPLE, Message.DEPRECATED_TYPE_TUPLE),
	'typing.List': ('list', Message.DEPRECATED_IMPORT_LIST, Message.DEPRECATED_TYPE_LIST),
	'typing.Dict': ('dict', Message.DEPRECATED_IMPORT_DICT, Message.DEPRECATED_TYPE_DICT),
	'typing.Set': ('set', Message.DEPRECATED_IMPORT_SET, Message.DEPRECATED_TYPE_SET),
	'typing.FrozenSet': ('frozenset', Message.DEPRECATED_IMPORT_FROZEN_SET, Message.DEPRECATED_TYPE_FROZEN_SET),
	'typing.Type': ('type', Message.DEPRECATED_IMPORT_TYPE, Message.DEPRECATED_TYPE_TYPE),
}

REPLACED_TYPES = {
	'typing.Deque': ('collections.deque', Message.REPLACED_IMPORT_DEQUE, Message.DEPRECATED_TYPE_DEQUE),
	'typing.DefaultDict': ('collections.defaultdict', Message.REPLACED_IMPORT_DEFAULT_DICT, Message.DEPRECATED_TYPE_DEFAULT_DICT),
	'typing.OrderedDict': ('collections.OrderedDict', Message.REPLACED_IMPORT_ORDERED_DICT, Message.DEPRECATED_TYPE_ORDERED_DICT),
	'typing.Counter': ('collections.Counter', Message.REPLACED_IMPORT_COUNTER, Message.DEPRECATED_TYPE_COUNTER),
	'typing.ChainMap': ('collections.ChainMap', Message.REPLACED_IMPORT_CHAIN_MAP, Message.DEPRECATED_TYPE_CHAIN_MAP),
	'typing.Awaitable': ('collections.abc.Awaitable', Message.REPLACED_IMPORT_AWAITABLE, Message.DEPRECATED_TYPE_AWAITABLE),
	'typing.Coroutine': ('collections.abc.Coroutine', Message.REPLACED_IMPORT_COROUTINE, Message.DEPRECATED_TYPE_COROUTINE),
	'typing.AsyncIterable': ('collections.abc.AsyncIterable', Message.REPLACED_IMPORT_ASYNC_ITERABLE, Message.DEPRECATED_TYPE_ASYNC_ITERABLE),
	'typing.AsyncIterator': ('collections.abc.AsyncIterator', Message.REPLACED_IMPORT_ASYNC_ITERATOR, Message.DEPRECATED_TYPE_ASYNC_ITERATOR),
	'typing.AsyncGenerator': ('collections.abc.AsyncGenerator', Message.REPLACED_IMPORT_ASYNC_GENERATOR, Message.DEPRECATED_TYPE_ASYNC_GENERATOR),
	'typing.Iterable': ('collections.abc.Iterable', Message.REPLACED_IMPORT_ITERABLE, Message.DEPRECATED_TYPE_ITERABLE),
	'typing.Iterator': ('collections.abc.Iterator', Message.REPLACED_IMPORT_ITERATOR, Message.DEPRECATED_TYPE_ITERATOR),
	'typing.Generator': ('collections.abc.Generator', Message.REPLACED_IMPORT_GENERATOR, Message.DEPRECATED_TYPE_GENERATOR),
	'typing.Reversible': ('collections.abc.Reversible', Message.REPLACED_IMPORT_REVERSIBLE, Message.DEPRECATED_TYPE_REVERSIBLE),
	'typing.Container': ('collections.abc.Container', Message.REPLACED_IMPORT_CONTAINER, Message.DEPRECATED_TYPE_CONTAINER),
	'typing.Collection': ('collections.abc.Collection', Message.REPLACED_IMPORT_COLLECTION, Message.DEPRECATED_TYPE_COLLECTION),
	'typing.Callable': ('collections.abc.Callable', Message.REPLACED_IMPORT_CALLABLE, Message.DEPRECATED_TYPE_CALLABLE),
	'typing.AbstractSet': ('collections.abc.Set', Message.REPLACED_IMPORT_ABSTRACT_SET, Message.DEPRECATED_TYPE_ABSTRACT_SET),
	'typing.MutableSet': ('collections.abc.MutableSet', Message.REPLACED_IMPORT_MUTABLE_SET, Message.DEPRECATED_TYPE_MUTABLE_SET),
	'typing.Mapping': ('collections.abc.Mapping', Message.REPLACED_IMPORT_MAPPING, Message.DEPRECATED_TYPE_MAPPING),
	'typing.MutableMapping': ('collections.abc.MutableMapping', Message.REPLACED_IMPORT_MUTABLE_MAPPING, Message.DEPRECATED_TYPE_MUTABLE_MAPPING),
	'typing.Sequence': ('collections.abc.Sequence', Message.REPLACED_IMPORT_SEQUENCE, Message.DEPRECATED_TYPE_SEQUENCE),
	'typing.MutableSequence': ('collections.abc.MutableSequence', Message.REPLACED_IMPORT_MUTABLE_SEQUENCE, Message.DEPRECATED_TYPE_MUTABLE_SEQUENCE),
	'typing.ByteString': ('collections.abc.ByteString', Message.REPLACED_IMPORT_BYTE_STRING, Message.DEPRECATED_TYPE_BYTE_STRING),
	'typing.MappingView': ('collections.abc.MappingView', Message.REPLACED_IMPORT_MAPPING_VIEW, Message.DEPRECATED_TYPE_MAPPING_VIEW),
	'typing.KeysView': ('collections.abc.KeysView', Message.REPLACED_IMPORT_KEYS_VIEW, Message.DEPRECATED_TYPE_KEYS_VIEW),
	'typing.ItemsView': ('collections.abc.ItemsView', Message.REPLACED_IMPORT_ITEMS_VIEW, Message.DEPRECATED_TYPE_ITEMS_VIEW),
	'typing.ValuesView': ('collections.abc.ValuesView', Message.REPLACED_IMPORT_VALUES_VIEW, Message.DEPRECATED_TYPE_VALUES_VIEW),
	'typing.ContextManager': ('contextlib.AbstractContextManager', Message.REPLACED_IMPORT_CONTEXT_MANAGER, Message.DEPRECATED_TYPE_CONTEXT_MANAGER),
	'typing.AsyncContextManager': ('contextlib.AbstractAsyncContextManager', Message.REPLACED_IMPORT_ASYNC_CONTEXT_MANAGER, Message.DEPRECATED_TYPE_ASYNC_CONTEXT_MANAGER),  # noqa: E501
	'typing.Pattern': ('re.Pattern', Message.REPLACED_IMPORT_PATTERN, Message.DEPRECATED_TYPE_PATTERN),
	'typing.Match': ('re.Match', Message.REPLACED_IMPORT_MATCH, Message.DEPRECATED_TYPE_MATCH),
}

REQUIRED_TYPES = {
	'tuple': ('typing.Tuple', Message.REQUIRED_TYPE_TUPLE),
	'list': ('typing.List', Message.REQUIRED_TYPE_LIST),
	'dict': ('typing.Dict', Message.REQUIRED_TYPE_DICT),
	'set': ('typing.Set', Message.REQUIRED_TYPE_SET),
	'frozenset': ('typing.FrozenSet', Message.REQUIRED_TYPE_FROZEN_SET),
	'type': ('typing.Type', Message.REQUIRED_TYPE_TYPE),
	'collections.deque': ('typing.Deque', Message.REQUIRED_TYPE_DEQUE),
	'collections.defaultdict': ('typing.DefaultDict', Message.REQUIRED_TYPE_DEFAULT_DICT),
	'collections.OrderedDict': ('typing.OrderedDict', Message.REQUIRED_TYPE_ORDERED_DICT),
	'collections.Counter': ('typing.Counter', Message.REQUIRED_TYPE_COUNTER),
	'collections.ChainMap': ('typing.ChainMap', Message.REQUIRED_TYPE_CHAIN_MAP),
	'collections.abc.Awaitable': ('typing.Awaitable', Message.REQUIRED_TYPE_AWAITABLE),
	'collections.abc.Coroutine': ('typing.Coroutine', Message.REQUIRED_TYPE_COROUTINE),
	'collections.abc.AsyncIterable': ('typing.AsyncIterable', Message.REQUIRED_TYPE_ASYNC_ITERABLE),
	'collections.abc.AsyncIterator': ('typing.AsyncIterator', Message.REQUIRED_TYPE_ASYNC_ITERATOR),
	'collections.abc.AsyncGenerator': ('typing.AsyncGenerator', Message.REQUIRED_TYPE_ASYNC_GENERATOR),
	'collections.abc.Iterable': ('typing.Iterable', Message.REQUIRED_TYPE_ITERABLE),
	'collections.abc.Iterator': ('typing.Iterator', Message.REQUIRED_TYPE_ITERATOR),
	'collections.abc.Generator': ('typing.Generator', Message.REQUIRED_TYPE_GENERATOR),
	'collections.abc.Reversible': ('typing.Reversible', Message.REQUIRED_TYPE_REVERSIBLE),
	'collections.abc.Container': ('typing.Container', Message.REQUIRED_TYPE_CONTAINER),
	'collections.abc.Collection': ('typing.Collection', Message.REQUIRED_TYPE_COLLECTION),
	'collections.abc.Callable': ('typing.Callable', Message.REQUIRED_TYPE_CALLABLE),
	'collections.abc.Set': ('typing.AbstractSet', Message.REQUIRED_TYPE_ABSTRACT_SET),
	'collections.abc.MutableSet': ('typing.MutableSet', Message.REQUIRED_TYPE_MUTABLE_SET),
	'collections.abc.Mapping': ('typing.Mapping', Message.REQUIRED_TYPE_MAPPING),
	'collections.abc.MutableMapping': ('typing.MutableMapping', Message.REQUIRED_TYPE_MUTABLE_MAPPING),
	'collections.abc.Sequence': ('typing.Sequence', Message.REQUIRED_TYPE_SEQUENCE),
	'collections.abc.MutableSequence': ('typing.MutableSequence', Message.REQUIRED_TYPE_MUTABLE_SEQUENCE),
	'collections.abc.ByteString': ('typing.ByteString', Message.REQUIRED_TYPE_BYTE_STRING),
	'collections.abc.MappingView': ('typing.MappingView', Message.REQUIRED_TYPE_MAPPING_VIEW),
	'collections.abc.KeysView': ('typing.KeysView', Message.REQUIRED_TYPE_KEYS_VIEW),
	'collections.abc.ItemsView': ('typing.ItemsView', Message.REQUIRED_TYPE_ITEMS_VIEW),
	'collections.abc.ValuesView': ('typing.ValuesView', Message.REQUIRED_TYPE_VALUES_VIEW),
	'contextlib.AbstractContextManager': ('typing.ContextManager', Message.REQUIRED_TYPE_CONTEXT_MANAGER),
	'contextlib.AbstractAsyncContextManager': ('typing.AsyncContextManager', Message.REQUIRED_TYPE_ASYNC_CONTEXT_MANAGER),
	're.Pattern': ('typing.Pattern', Message.REQUIRED_TYPE_PATTERN),
	're.Match': ('typing.Match', Message.REQUIRED_TYPE_MATCH),
}

Violation = Tuple[ast.AST, Message, Dict[str, str]]


class AnnotationVisitor(ast.NodeVisitor):
	"""Annotation visitor."""

	allow_type_alias: bool
	union_paren: str
	type_map: dict[str, str]
	postponed: list[Violation]
	deprecated_imports: dict[str, list[Violation]]
	deprecated: list[Violation]
	required: list[Violation]
	union_imports: dict[str, list[Violation]]
	union: list[Violation]

	def __init__(self, allow_type_alias: bool, union_paren: str) -> None:
		self.allow_type_alias = allow_type_alias
		self.union_paren = union_paren
		self.type_map = {
			'tuple': 'tuple',
			'list': 'list',
			'dict': 'dict',
			'set': 'set',
			'frozenset': 'frozenset',
			'type': 'type',
		}
		self.postponed = []
		self.deprecated_imports = {}
		self.deprecated = []
		self.required = []
		self.union_imports = {}
		self.union = []

	def _name(self, node: ast.AST) -> str:
		if (isinstance(node, ast.Subscript)):
			return self._name(node.value)
		if (isinstance(node, ast.Name)):
			return node.id
		if (isinstance(node, ast.Attribute)):
			return f'{self._name(node.value)}.{node.attr}'
		return ''

	def _add_deprecated_import(self, node: ast.ImportFrom, type_name: str, alias_name: str) -> None:
		if (alias_name not in self.deprecated_imports):
			self.deprecated_imports[alias_name] = []
		replacement, message, _ = REPLACED_TYPES[type_name] if (type_name in REPLACED_TYPES) else DEPRECATED_TYPES[type_name]
		self.deprecated_imports[alias_name].append((node, message, {'name': type_name, 'replacement': replacement}))

	def _add_union_import(self, node: ast.ImportFrom, type_name: str, alias_name: str) -> None:
		if (alias_name not in self.union_imports):
			self.union_imports[alias_name] = []
		self.union_imports[alias_name].append((node, Message.UNION_IMPORT, {'name': type_name}))

	def _remove_import_violations(self, node: Optional[ast.AST]) -> None:
		"""Find types used in type aliases, remove from deprecated_imports and union_imports."""
		if (isinstance(node, (ast.Name, ast.Attribute, ast.Subscript))):
			name = self._name(node)
			if (name in self.deprecated_imports):
				del self.deprecated_imports[name]
			if (name in self.union_imports):
				del self.union_imports[name]

		if (isinstance(node, ast.Subscript)):
			value = node.slice.value if (isinstance(node.slice, ast.Index)) else node.slice
			if (isinstance(value, ast.Tuple)):
				for item in value.elts:
					self._remove_import_violations(item)
			else:
				self._remove_import_violations(value)

	def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
		for alias in node.names:
			import_name = (alias.asname or alias.name)
			if ('typing' == alias.name):
				for type_name in TYPING_TYPES:
					self.type_map[f'{import_name}.{type_name}'] = f'typing.{type_name}'
			elif ('typing_extensions' == alias.name):
				for type_name in TYPING_EXTENSION_TYPES:
					self.type_map[f'{import_name}.{type_name}'] = f'typing_extensions.{type_name}'
			elif ('collections' == alias.name):
				for type_name in COLLECTIONS_TYPES:
					self.type_map[f'{import_name}.{type_name}'] = f'collections.{type_name}'
			elif ('collections.abc' == alias.name):
				for type_name in COLLECTIONS_ABC_TYPES:
					self.type_map[f'{import_name}.{type_name}'] = f'collections.abc.{type_name}'
			elif ('contextlib' == alias.name):
				for type_name in CONTEXTLIB_TYPES:
					self.type_map[f'{import_name}.{type_name}'] = f'contextlib.{type_name}'
			elif ('re' == alias.name):
				for type_name in CONTEXTLIB_TYPES:
					self.type_map[f'{import_name}.{type_name}'] = f're.{type_name}'

	def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
		if ('typing' == node.module):
			for alias in node.names:
				type_name = f'typing.{alias.name}'
				alias_name = (alias.asname or alias.name)
				self.type_map[alias_name] = type_name
				if ((type_name in DEPRECATED_TYPES) or (type_name in REPLACED_TYPES)):
					self._add_deprecated_import(node, type_name, alias_name)
				elif ('typing.Union' == type_name):
					self._add_union_import(node, type_name, alias_name)
		elif ('typing_extensions' == node.module):
			for alias in node.names:
				if (alias.name in TYPING_EXTENSION_TYPES):
					self.type_map[alias.asname or alias.name] = f'typing_extensions.{alias.name}'
		elif ('collections' == node.module):
			for alias in node.names:
				if (alias.name in COLLECTIONS_TYPES):
					self.type_map[alias.asname or alias.name] = f'collections.{alias.name}'
		elif ('collections.abc' == node.module):
			for alias in node.names:
				if (alias.name in COLLECTIONS_ABC_TYPES):
					self.type_map[alias.asname or alias.name] = f'collections.abc.{alias.name}'
		elif ('contextlib' == node.module):
			for alias in node.names:
				if (alias.name in CONTEXTLIB_TYPES):
					self.type_map[alias.asname or alias.name] = f'contextlib.{alias.name}'
		elif ('re' == node.module):
			for alias in node.names:
				if (alias.name in RE_TYPES):
					self.type_map[alias.asname or alias.name] = f're.{alias.name}'

	def _check_postponed(self, annotation: Optional[ast.AST], message: Message) -> Iterator[Violation]:
		if (isinstance(annotation, ast.Constant)):
			if ((annotation.value is None) or isinstance(annotation.value, type(Ellipsis))):
				return
			yield (annotation, message, {'value': annotation.value})
		elif (isinstance(annotation, ast.Subscript)):
			if (isinstance(annotation.value, (ast.Name, ast.Attribute))):  # skip Literals
				name = self._name(annotation)
				type_name = self.type_map.get(name)
				if (type_name in LITERALS):
					return

			value = annotation.slice.value if (isinstance(annotation.slice, ast.Index)) else annotation.slice
			if (isinstance(value, ast.Tuple)):
				for item in value.elts:
					yield from self._check_postponed(item, message)
			else:
				yield from self._check_postponed(value, message)
		else:
			try:
				if (isinstance(annotation, ast.Str)):  # python3.7
					if (annotation.s is None):
						return
					yield (annotation, message, {'value': annotation.s})
			except AttributeError:
				pass

	def _check_deprecated(self, annotation: Optional[ast.AST]) -> Iterator[Violation]:
		if (isinstance(annotation, (ast.Name, ast.Attribute, ast.Subscript))):
			name = self._name(annotation)
			type_name = self.type_map.get(name)
			if ((type_name in DEPRECATED_TYPES) or (type_name in REPLACED_TYPES)):
				replacement, _, message = DEPRECATED_TYPES[type_name] if (type_name in DEPRECATED_TYPES) else REPLACED_TYPES[type_name]
				yield (annotation, message, {'name': name, 'replacement': replacement})

		if (isinstance(annotation, ast.Subscript)):
			value = annotation.slice.value if (isinstance(annotation.slice, ast.Index)) else annotation.slice
			if (isinstance(value, ast.Tuple)):
				for item in value.elts:
					yield from self._check_deprecated(item)
			else:
				yield from self._check_deprecated(value)

	def _check_required(self, annotation: Optional[ast.AST]) -> Iterator[Violation]:
		if (isinstance(annotation, (ast.Name, ast.Attribute, ast.Subscript))):
			name = self._name(annotation)
			type_name = self.type_map.get(name)
			if (type_name in REQUIRED_TYPES):
				replacement, message = REQUIRED_TYPES[type_name]
				yield (annotation, message, {'name': name, 'replacement': replacement})

		if (isinstance(annotation, ast.Subscript)):
			value = annotation.slice.value if (isinstance(annotation.slice, ast.Index)) else annotation.slice
			if (isinstance(value, ast.Tuple)):
				for item in value.elts:
					yield from self._check_required(item)
			else:
				yield from self._check_required(value)

	def _check_union(self, annotation: Optional[ast.AST]) -> Iterator[Violation]:
		if (isinstance(annotation, (ast.Name, ast.Attribute, ast.Subscript))):
			name = self._name(annotation)
			type_name = self.type_map.get(name)
			if ('typing.Union' == type_name):
				yield (annotation, Message.UNION_TYPE, {'name': name})

		if (isinstance(annotation, ast.Subscript)):
			value = annotation.slice.value if (isinstance(annotation.slice, ast.Index)) else annotation.slice
			if (isinstance(value, ast.Tuple)):
				for item in value.elts:
					yield from self._check_union(item)
			else:
				yield from self._check_union(value)

	def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
		if (self.allow_type_alias):
			self._remove_import_violations(node.value)
			self.required.extend(self._check_required(node.value))
		else:
			self.deprecated.extend(self._check_deprecated(node.value))
			self.union.extend(self._check_union(node.value))

	def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
		self.postponed.extend(self._check_postponed(node.annotation, Message.POSTPONED_ASSIGN_TYPE))
		self.deprecated.extend(self._check_deprecated(node.annotation))
		self.union.extend(self._check_union(node.annotation))

	def visit_arg(self, node: ast.arg) -> None:
		self.postponed.extend(self._check_postponed(node.annotation, Message.POSTPONED_ARG_TYPE))
		self.deprecated.extend(self._check_deprecated(node.annotation))
		self.union.extend(self._check_union(node.annotation))

	def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
		self.generic_visit(node)
		self.postponed.extend(self._check_postponed(node.returns, Message.POSTPONED_RETURN_TYPE))
		self.deprecated.extend(self._check_deprecated(node.returns))
		self.union.extend(self._check_union(node.returns))


class AnnotationChecker(Checker):
	"""Annotation checker."""

	tree: ast.AST
	postponed: bool
	deprecated: bool
	type_alias: bool
	union: bool

	def __init__(self, tree: ast.AST) -> None:
		self.tree = tree
		self.postponed = ('always' == self.postponed_option)
		self.deprecated = ('always' == self.deprecated_option)
		self.type_alias = ('always' == self.type_alias_option)
		self.union = ('always' == self.union_option)

	def __iter__(self) -> Iterator[ASTResult]:
		"""Primary call from flake8, yield error messages."""
		future_visitor = FutureVisitor()
		future_visitor.visit(self.tree)

		if ((not self.postponed) and ('never' != self.postponed_option)):
			self.postponed = future_visitor.enabled

		if ((not self.deprecated) and ('never' != self.deprecated_option)):
			self.deprecated = (future_visitor.enabled or (sys.version_info >= (3, 9)))

		if ((not self.type_alias) and ('never' != self.type_alias_option)):
			self.type_alias = (sys.version_info < (3, 9))

		if ((not self.type_alias) and ('never' != self.type_alias_option)):
			self.type_alias = (sys.version_info < (3, 9))

		if ((not self.union) and ('never' != self.union_option)):
			self.union = (future_visitor.enabled or (sys.version_info >= (3, 10)))

		annotation_visitor = AnnotationVisitor(self.type_alias, self.union_paren_option)
		annotation_visitor.visit(self.tree)

		if (self.postponed):
			for node, message, kwargs in annotation_visitor.postponed:
				yield self._ast_node_message(node, message, **kwargs)

		if (self.deprecated):
			for violations in annotation_visitor.deprecated_imports.values():
				for node, message, kwargs in violations:
					yield self._ast_node_message(node, message, **kwargs)
			for node, message, kwargs in annotation_visitor.deprecated:
				yield self._ast_node_message(node, message, **kwargs)
			for node, message, kwargs in annotation_visitor.required:
				yield self._ast_node_message(node, message, **kwargs)

		if (self.union):
			for violations in annotation_visitor.union_imports.values():
				for node, message, kwargs in violations:
					yield self._ast_node_message(node, message, **kwargs)
			for node, message, kwargs in annotation_visitor.union:
				yield self._ast_node_message(node, message, **kwargs)
