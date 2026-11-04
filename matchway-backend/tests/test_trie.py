from app.engine.trie import Trie

def test_trie_basic_sharing():
    trie = Trie()
    route1 = ["Campus Gate", "Station Road", "City Mall"]
    route2 = ["Campus Gate", "Station Road", "Airport"]

    trie.insert(route1, "rider1")
    trie.insert(route2, "rider2")

    # Both share the first two stops
    prefix = ["Campus Gate", "Station Road"]
    riders = trie.riders_with_prefix(prefix)
    assert "rider1" in riders
    assert "rider2" in riders
    assert len(riders) == 2

def test_trie_no_match():
    trie = Trie()
    trie.insert(["Campus Gate", "Station Road"], "rider1")

    # Route that doesn't exist
    riders = trie.riders_with_prefix(["Unknown Stop"])
    assert riders == []

def test_trie_prefix_and_lcp():
    trie = Trie()
    route = ["Campus Gate", "Station Road", "City Mall"]
    trie.insert(route, "rider1")

    # Prefix match
    assert trie.riders_with_prefix(["Campus Gate"]) == ["rider1"]

    # Longest Common Prefix
    assert trie.longest_common_prefix(["Campus Gate", "Station Road", "Unknown"]) == 2
    assert trie.longest_common_prefix(["Unknown"]) == 0

def test_trie_removal():
    trie = Trie()
    route = ["Campus Gate", "Station Road"]
    trie.insert(route, "rider1")
    trie.insert(route, "rider2")

    assert len(trie.riders_with_prefix(route)) == 2

    trie.remove(route, "rider1")
    riders = trie.riders_with_prefix(route)
    assert "rider2" in riders
    assert "rider1" not in riders
    assert len(riders) == 1

if __name__ == "__main__":
    test_trie_basic_sharing()
    test_trie_no_match()
    test_trie_prefix_and_lcp()
    test_trie_removal()
    print("All tests passed!")
