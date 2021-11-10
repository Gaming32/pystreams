from streams import Stream, collectors


def test():
    # print(Stream.iterate('a', (lambda x: chr(ord(x) + 1)))
    #             .limit(4)
    #             .sum())
    print(Stream.range(5)
                .collect(collectors.to_list()))

test()
