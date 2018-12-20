from typing import List

class Decider(object):

    # Constructor
    def __init__(self, name: str):
        self.name = name

    # Given a set of candidate production rules and a 'trail' containing the previous productions rules,
    # choose one of the candidate production rules and return it.
    def decide(trail: List[str], candidates: List[str]) -> str:
        return ""

    def decide_sketch(trail: List[str], candidates: List[str], child: int) -> str:
        return ""
