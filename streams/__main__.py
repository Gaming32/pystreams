from streams import Stream


def test():
    print(Stream.iterate('a', (lambda x: chr(ord(x) + 1)))
                .limit(4)
                .sum())

test()
