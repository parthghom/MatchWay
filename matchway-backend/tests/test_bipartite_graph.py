import random
import itertools
from app.engine.bipartite_graph import BipartiteGraph

def test_bg_empty():
    bg = BipartiteGraph()
    assert bg.max_matching() == []

def test_bg_simple():
    bg = BipartiteGraph()
    bg.add_left("d1")
    bg.add_right("r1")
    bg.add_edge("d1", "r1")
    matching = bg.max_matching()
    assert len(matching) == 1
    assert matching[0] == ("d1", "r1")

def test_bg_augmenting_path():
    # Case: d1 -> r1, r2; d2 -> r1
    # Greedy choice of d1-r1 would block d2, but augmenting path finds d1-r2 and d2-r1.
    bg = BipartiteGraph()
    bg.add_left("d1")
    bg.add_left("d2")
    bg.add_right("r1")
    bg.add_right("r2")
    bg.add_edge("d1", "r1")
    bg.add_edge("d1", "r2")
    bg.add_edge("d2", "r1")

    matching = bg.max_matching()
    assert len(matching) == 2

def test_bg_key_error():
    bg = BipartiteGraph()
    bg.add_left("d1")
    bg.add_right("r1")
    try:
        bg.add_edge("d1", "r2")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass

def test_bg_random_brute_force():
    for _ in range(50):
        bg = BipartiteGraph()
        num_l = random.randint(1, 5)
        num_r = random.randint(1, 5)
        lefts = [f"l{i}" for i in range(num_l)]
        rights = [f"r{i}" for i in range(num_r)]

        for l in lefts: bg.add_left(l)
        for r in rights: bg.add_right(r)

        # Random edges
        edges = []
        for l in lefts:
            for r in rights:
                if random.random() < 0.3:
                    bg.add_edge(l, r)
                    edges.append((l, r))

        matching = bg.max_matching()

        # Brute force: check all permutations of left nodes mapping to right nodes
        # Since the size is very small (max 5x5), we can check all assignments.
        max_size = 0
        # We want to find a set of edges such that no two share a vertex.
        # For small N, we can iterate through all subsets of edges.
        from itertools import combinations
        for r in range(1, len(edges) + 1):
            for combo in combinations(edges, r):
                # Check if combo is a valid matching
                ls = [e[0] for e in combo]
                rs = [e[1] for e in combo]
                if len(set(ls)) == len(ls) and len(set(rs)) == len(rs):
                    max_size = max(max_size, len(combo))

        assert len(matching) == max_size

if __name__ == "__main__":
    test_bg_empty()
    test_bg_simple()
    test_bg_augmenting_path()
    test_bg_key_error()
    test_bg_random_brute_force()
    print("All tests passed!")
