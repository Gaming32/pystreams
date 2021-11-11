from typing import Iterator
from streams import Stream, collectors


def get_factors(i: int) -> Iterator[int]:
    return (Stream.range(2, i)
                  .filter(lambda x: (i % x) == 0))


def is_prime(i: int) -> bool:
    return Stream(get_factors(i)).get_one() is None


def print_primes(i: int):
    print(Stream.range(1, i + 1)
                .filter(is_prime)
                .map(str)
                .collect(collectors.joining(' ', '[', ']')))


def test():
    print(Stream.iterate('a', (lambda x: chr(ord(x) + 1)))
                .limit(4)
                .sum())
    print(Stream.range(10)
                .collect(collectors.grouping_by(lambda x: x % 3)))
    print(Stream.range(5)
                .map(str)
                .collect(collectors.joining(', ', '[', ']')))
    print_primes(7)
    print(Stream.concat(Stream.range(3), Stream.range(7, 10))
                .to_list())

test()
