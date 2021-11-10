"""Python version of Java streams"""


import operator
from typing import (TYPE_CHECKING, Any, Callable, Generic, Iterable, Iterator,
                    Optional, TypeVar, Union, final)

if TYPE_CHECKING:
    from _typeshed import SupportsLessThan

if TYPE_CHECKING:
    _T_SupportsLessThan = TypeVar('_T_SupportsLessThan', bound=SupportsLessThan)
_T = TypeVar('_T')
_R = TypeVar('_R')


@final
class Stream(Generic[_T]):
    it: Iterator[_T]

    def __init__(self, it: Union[Iterable[_T], Iterator[_T]]) -> None:
        if hasattr(it, '__iter__'):
            it = iter(it)
        self.it = it # type: ignore

    def __iter__(self) -> Iterator[_T]:
        return self.it

    def __next__(self) -> _T:
        return self.it.__next__()

    def all_match(self, predicate: Callable[[_T], bool]) -> bool:
        return all(predicate(x) for x in self.it)

    def any_match(self, predicate: Callable[[_T], bool]) -> bool:
        return any(predicate(x) for x in self.it)

    @staticmethod
    def concat(a: 'Stream[_T]', b: 'Stream[_T]') -> 'Stream[_T]':
        def it():
            yield from a
            yield from b
        return Stream(it())

    def count(self) -> int:
        return sum(1 for _ in self.it)

    def distinct(self) -> 'Stream[_T]':
        def it():
            elems = set()
            for elem in self.it:
                if elem not in elems:
                    elems.add(elem)
                    yield elem
        return Stream(it())

    @staticmethod
    def empty() -> 'Stream':
        return Stream(())

    def filter(self, predicate: Callable[[_T], bool]) -> 'Stream[_T]':
        return Stream(filter(predicate, self.it))

    def find_any(self) -> Optional[_T]:
        return next(self.it, None)

    def find_first(self) -> Optional[_T]:
        return next(self.it, None)

    def flat_map(self, mapper: Callable[[_T], Union[Iterable[_R], Iterator[_R]]]) -> 'Stream[_R]':
        def it():
            for v in self.it:
                yield from mapper(v)
        return Stream(it())

    def for_each(self, action: Callable[[_T], Any]) -> None:
        for v in self.it:
            action(v)

    @staticmethod
    def iterate(seed: _T, f: Callable[[_T], _T]) -> 'Stream[_T]':
        def it():
            x = seed
            while True:
                yield x
                x = f(x)
        return Stream(it())

    def limit(self, max_size: int) -> 'Stream[_T]':
        def it():
            for _ in range(max_size):
                yield next(self.it)
        return Stream(it())

    def map(self, mapper: Callable[[_T], _R]) -> 'Stream[_R]':
        return Stream(map(mapper, self.it))

    def max(self: 'Stream[_T_SupportsLessThan]') -> '_T_SupportsLessThan':
        return max(self.it)

    def min(self: 'Stream[_T_SupportsLessThan]') -> '_T_SupportsLessThan':
        return min(self.it)

    def none_match(self) -> bool:
        return not any(self.it)

    @staticmethod
    def of(*values: _T) -> 'Stream[_T]':
        return Stream(values)

    def peek(self, action: Callable[[_T], Any]) -> 'Stream[_T]':
        def it():
            for v in self.it:
                action(v)
                yield v
        return Stream(it())

    def skip(self, n: int) -> 'Stream[_T]':
        try:
            for _ in range(n):
                next(self.it)
        except StopIteration:
            pass
        return Stream(self.it)

    def sorted(self: 'Stream[_T_SupportsLessThan]') -> 'Stream[_T_SupportsLessThan]':
        return Stream(sorted(self.it))

    def to_list(self) -> list[_T]:
        return list(self.it)

    def iterator(self) -> Iterator[_T]:
        return self.it

    def average(self):
        try:
            sum = next(self.it)
        except StopIteration:
            return None
        count = 1
        for v in self.it:
            sum += v
            count += 1
        return sum / count

    def sum(self):
        return self.reduce(operator.add)

    @staticmethod
    def range(start: int, stop: Optional[int] = None, step: Optional[int] = None) -> 'Stream[int]':
        if stop is None:
            r = range(start)
        elif step is None:
            r = range(start, stop)
        else:
            r = range(start, stop, step)
        return Stream(r)

    def reduce(self, accumulator: Callable[[_T, _T], _T]) -> Optional[_T]:
        try:
            result = next(self.it)
        except StopIteration:
            return None
        for v in self.it:
            result = accumulator(result, v)
        return result


def test():
    print(Stream.iterate('a', (lambda x: chr(ord(x) + 1)))
                .limit(4)
                .sum())
    print(Stream.range(5)
                .average())


if __name__ == '__main__':
    test()
