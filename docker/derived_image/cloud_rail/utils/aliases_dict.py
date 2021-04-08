from typing import TypeVar, Generic, Optional, Callable, Set

from environment_context.data.main.mergeable import Mergeable

_VT = TypeVar('_VT', bound=Mergeable)


class AliasesDict(Generic[_VT]):
    '''
    A Multi-key dictionary, where the keys are the 'aliases' attribute for Mergeable instances
    '''
    __marker = object()

    def __init__(self, *args: _VT):
        self._values = set(args)
        self._dict = {alias: arg for arg in args for alias in arg.aliases}

    def update(self, *items: _VT) -> None:
        for item in items:
            self._values.add(item)
            self._dict.update({alias: item for alias in item.aliases})

    def pop(self, alias: str, default=__marker) -> Optional[_VT]:
        try:
            value = self._dict.pop(alias)
            for value_alias in value.aliases:
                self._dict.pop(value_alias, None)
            self._values.remove(value)
            return value
        except KeyError as ex:
            if default is self.__marker:
                raise ex
            return default

    def __getitem__(self, key: str) -> _VT:
        return self._dict[key]

    def get(self, key, default=None) -> Optional[_VT]:
        try:
            return self._dict[key]
        except (KeyError, TypeError):
            return default

    def values(self) -> Set[_VT]:
        return self._values.copy()

    def keys(self):
        return self._dict.keys()

    def __repr__(self):
        return self._dict.__repr__()

    def where(self, condition: Callable[[_VT], bool]) -> Set[_VT]:
        return {val for val in self._values if condition(val)}

    def remove(self, *items: _VT) -> None:
        for item in items:
            if not any(self.pop(alias, None) for alias in item.aliases):
                raise ValueError(f'Item with aliases: [{", ".join(item.aliases)}] was not found')

    def __add__(self, other: 'AliasesDict[_VT]') -> 'AliasesDict[_VT]':
        return AliasesDict(*self._values, *other.values())

    def __iter__(self):
        return self.values().__iter__()

    def __len__(self):
        return len(self.values())
