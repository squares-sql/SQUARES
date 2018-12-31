from itertools import combinations, chain


def enum_set_domain(elem_domain, max_len):
    itr = chain.from_iterable(
        [combinations(elem_domain, x) for x in range(1, max_len + 1)])
    return [list(x) for x in itr]
