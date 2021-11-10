"""Python version of Java streams"""


import abc
import operator
from typing import (TYPE_CHECKING, Any, Callable, Generic, Iterable, Iterator,
                    Optional, Tuple, TypeVar, Union, cast, final)

if TYPE_CHECKING:
    from _typeshed import SupportsLessThan

_T = TypeVar('_T')
_R = TypeVar('_R')
_U = TypeVar('_U')
_A = TypeVar('_A')

if TYPE_CHECKING:
    _T_SupportsLessThan = TypeVar('_T_SupportsLessThan', bound=SupportsLessThan)

__all__ = ['Collector', 'Stream']


class Collector(abc.ABC, Generic[_T, _A, _R]):
    @abc.abstractmethod
    def supplier(self) -> _A:
        pass

    @abc.abstractmethod
    def accumulator(self, result: _A, value: _T) -> Any:
        pass

    @abc.abstractmethod
    def finisher(self, result: _A) -> _R:
        pass

    @staticmethod
    def of(supplier: Callable[[], _R], accumulator: Callable[[_R, _T], Any]) -> 'Collector[_T, _R, _R]':
        class WrapperCollector(Collector):
            def supplier(self) -> _R:
                return supplier()
            def accumulator(self, result: _R, value: _T) -> Any:
                return accumulator(result, value)
            def finisher(self, result: _R) -> _R:
                return result
        return WrapperCollector()


@final
class Stream(Generic[_T]):
    it: Iterator[_T]

    def __init__(self, it: Union[Iterable[_T], Iterator[_T]]) -> None:
        if hasattr(it, '__iter__'):
            it = iter(it)
        self.it = cast(Iterator[_T], it)

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

    def get_one(self) -> Optional[_T]:
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

    def reduce_identity(self, identity: _U, accumulator: Callable[[_U, _T], _U]) -> _U:
        for v in self.it:
            identity = accumulator(identity, v)
        return identity

    def reduce(self, accumulator: Callable[[_T, _T], _T]) -> Optional[_T]:
        try:
            result = next(self.it)
        except StopIteration:
            return None
        return self.reduce_identity(result, accumulator)

    def collect_simple(self, supplier: Callable[[], _R], accumulator: Callable[[_R, _T], Any]) -> _R:
        return self.collect(Collector.of(supplier, accumulator))

    def collect(self, collector: Collector[_T, Any, _R]) -> _R:
        result = collector.supplier()
        for value in self.it:
            collector.accumulator(result, value)
        return collector.finisher(result)
