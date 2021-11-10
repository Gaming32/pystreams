from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

from .streams import Collector, Stream

_T = TypeVar('_T')
_A = TypeVar('_A')
_R = TypeVar('_R')
_RR = TypeVar('_RR')
_K = TypeVar('_K')
_U = TypeVar('_U')
_D = TypeVar('_D')

class _NOTHING_CLASS: pass
_NOTHING = _NOTHING_CLASS()

class _Wrapper(Generic[_T]):
    value: _T

    def __init__(self, value: _T) -> None:
        self.value = value


class collecting_and_then(Collector[_T, _A, _RR], Generic[_T, _A, _R, _RR]):
    downstream: Collector[_T, _A, _R]
    new_finisher: Callable[[_R], _RR]

    def __init__(self, downstream: Collector[_T, _A, _R], finisher: Callable[[_R], _RR]) -> None:
        self.downstream = downstream
        self.new_finisher = finisher

    def supplier(self) -> _A:
        return self.downstream.supplier()

    def accumulator(self, result: _A, value: _T) -> Any:
        return self.downstream.accumulator(result, value)

    def finisher(self, result: _A) -> _RR:
        return self.new_finisher(self.downstream.finisher(result))


class grouping_by(Collector[_T, dict[_K, list[_T]], dict[_K, list[_T]]], Generic[_T, _K]):
    classifier: Callable[[_T], _K]

    def __init__(self, classifier: Callable[[_T], _K]) -> None:
        self.classifier = classifier

    def supplier(self) -> dict[_K, list[_T]]:
        return {}

    def accumulator(self, result: dict[_K, list[_T]], value: _T) -> None:
        group = self.classifier(value)
        result.setdefault(group, []).append(value)

    def finisher(self, result: dict[_K, list[_T]]) -> dict[_K, list[_T]]:
        return result


class joining(Collector[str, List[str], str]):
    delimiter: str
    prefix: str
    suffix: str

    def __init__(self, delimiter: str = '', prefix: str = '', suffix: str = '') -> None:
        self.delimiter = delimiter
        self.prefix = prefix
        self.suffix = suffix

    def supplier(self) -> List[str]:
        return []

    def accumulator(self, result: List[str], value: str) -> None:
        result.append(value)

    def finisher(self, result: List[str]) -> str:
        return self.suffix + self.delimiter.join(result) + self.suffix


class mapping(Collector[_T, _A, _R], Generic[_T, _U, _A, _R]):
    mapper: Callable[[_T], _U]
    downstream: Collector[_U, _A, _R]

    def __init__(self, mapper: Callable[[_T], _U], downstream: Collector[_U, _A, _R]) -> None:
        self.mapper = mapper
        self.downstream = downstream

    def supplier(self) -> _A:
        return self.downstream.supplier()

    def accumulator(self, result: _A, value: _T) -> Any:
        return self.downstream.accumulator(result, self.mapper(value))

    def finisher(self, result: _A) -> _R:
        return self.downstream.finisher(result)


class partition(Collector[_T, Tuple[List[_T], List[_T]], Tuple[List[_T], List[_T]]], Generic[_T]):
    predicate: Callable[[_T], bool]

    def __init__(self, predicate: Callable[[_T], bool]) -> None:
        self.predicate = predicate

    def supplier(self) -> Tuple[List[_T], List[_T]]:
        return ([], [])

    def accumulator(self, result: Tuple[List[_T], List[_T]], value: _T) -> None:
        partition = self.predicate(value)
        result[partition].append(value)

    def finisher(self, result: Tuple[List[_T], List[_T]]) -> Tuple[List[_T], List[_T]]:
        return result


class partition_downstream(Collector[_T, Tuple[List[_T], List[_T]], Tuple[_D, _D]], Generic[_T, _D, _A]):
    predicate: Callable[[_T], bool]
    downstream: Collector[_T, _A, _D]

    def __init__(self, predicate: Callable[[_T], bool], downstream: Collector[_T, _A, _D]) -> None:
        self.predicate = predicate
        self.downstream = downstream

    def supplier(self) -> Tuple[List[_T], List[_T]]:
        return ([], [])

    def accumulator(self, result: Tuple[List[_T], List[_T]], value: _T) -> None:
        partition = self.predicate(value)
        result[partition].append(value)

    def finisher(self, result: Tuple[List[_T], List[_T]]) -> Tuple[_D, _D]:
        return (
            Stream(result[0]).collect(self.downstream),
            Stream(result[1]).collect(self.downstream)
        )


class reducing(Collector[_T, _Wrapper[Union[_T, _NOTHING_CLASS]], Optional[_T]], Generic[_T]):
    op: Callable[[_T, _T], _T]

    def __init__(self, op: Callable[[_T, _T], _T]) -> None:
        self.op = op

    def supplier(self) -> _Wrapper[_NOTHING_CLASS]:
        return _Wrapper(_NOTHING)

    def accumulator(self, result: _Wrapper[Union[_T, _NOTHING_CLASS]], value: _T) -> None:
        if result.value is _NOTHING:
            result.value = value
        else:
            result.value = self.op(result.value, value)

    def finisher(self, result: _Wrapper[Union[_T, _NOTHING_CLASS]]) -> Optional[_T]:
        if result.value is _NOTHING:
            return None
        assert not isinstance(result.value, _NOTHING_CLASS)
        return result.value


class reducing_mapper(Collector[_T, _Wrapper[_U], _U], Generic[_T, _U]):
    identity: _U
    mapper: Callable[[_T], _U]
    op: Callable[[_U, _U], _U]

    def __init__(self, identity: _U, mapper: Callable[[_T], _U], op: Callable[[_U, _U], _U]) -> None:
        self.identity = identity
        self.mapper = mapper
        self.op = op

    def supplier(self) -> _Wrapper[_U]:
        return _Wrapper(self.identity)

    def accumulator(self, result: _Wrapper[_U], value: _T) -> None:
        result.value = self.op(result.value, self.mapper(value))

    def finisher(self, result: _Wrapper[_U]) -> _U:
        return result.value


def reducing_identity(identity: _T, op: Callable[[_T, _T], _T]) -> Collector[_T, Any, _T]:
    return reducing_mapper(identity, (lambda x: x), op)


def to_list() -> Collector[_T, Any, List[_T]]:
    return Collector.of(list, list.append)


class to_dict(Collector[_T, Dict[_K, _U], Dict[_K, _U]], Generic[_T, _K, _U]):
    key_mapper: Callable[[_T], _K]
    value_mapper: Callable[[_T], _U]

    def __init__(self, key_mapper: Callable[[_T], _K], value_mapper: Callable[[_T], _U]) -> None:
        self.key_mapper = key_mapper
        self.value_mapper = value_mapper

    def supplier(self) -> Dict[_K, _U]:
        return {}

    def accumulator(self, result: Dict[_K, _U], value: _T) -> None:
        key = self.key_mapper(value)
        if key in result:
            raise ValueError('duplicate key')
        result[key] = self.value_mapper(value)

    def finisher(self, result: Dict[_K, _U]) -> Dict[_K, _U]:
        return result


def to_set() -> Collector[_T, Any, Set[_T]]:
    return Collector.of(set, set.add)
