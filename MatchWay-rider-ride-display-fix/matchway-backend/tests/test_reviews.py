from app.engine.reviews import ReviewService
import pytest

def test_review_score_ema():
    service = ReviewService()
    # New rider (starts at 3.0). 5 stars: 0.3*5 + 0.7*3.0 = 1.5 + 2.1 = 3.6
    service.submit_review("r1", "r2", 5)
    assert service.get_score("r2") == 3.6

    # Second 5 stars: 0.3*5 + 0.7*3.6 = 1.5 + 2.52 = 4.02
    service.submit_review("r3", "r2", 5)
    assert service.get_score("r2") == 4.02

    # 30 more five-star reviews should converge to 5.0 but not exceed it
    for i in range(30):
        service.submit_review(f"user{i}", "r2", 5)
    assert service.get_score("r2") <= 5.0
    assert service.get_score("r2") > 4.9

def test_review_blocking():
    service = ReviewService()
    # 1 star blocks in both directions
    service.submit_review("r1", "r2", 1)
    assert service.is_blocked("r1", "r2") is True
    assert service.is_blocked("r2", "r1") is True
    # and it still goes through the EMA: 0.3*1 + 0.7*3.0 = 2.4
    assert service.get_score("r2") == 2.4

def test_review_unsafe():
    service = ReviewService()
    # 2 stars add to unsafe count
    service.submit_review("r1", "r2", 2)
    assert service.unsafe_count("r2") == 1
    assert service.is_unsafe("r2") is False

    service.submit_review("r3", "r2", 2)
    assert service.unsafe_count("r2") == 2
    assert service.is_unsafe("r2") is False

    service.submit_review("r4", "r2", 2)
    assert service.unsafe_count("r2") == 3
    assert service.is_unsafe("r2") is True

def test_review_validation():
    service = ReviewService()
    # Stars 0, 6, 3.5, and "5" should raise ValueError
    with pytest.raises(ValueError):
        service.submit_review("r1", "r2", 0)
    with pytest.raises(ValueError):
        service.submit_review("r1", "r2", 6)
    with pytest.raises(ValueError):
        service.submit_review("r1", "r2", 3.5)
    with pytest.raises(ValueError):
        service.submit_review("r1", "r2", "5")

    # Reviewing self should raise ValueError
    with pytest.raises(ValueError):
        service.submit_review("r1", "r1", 5)

def test_review_unknown_rider():
    service = ReviewService()
    assert service.get_score("unknown") == 3.0


def test_every_star_value_follows_the_ema_formula():
    # S_new = 0.3 * stars + 0.7 * S_old, starting from 3.0
    for stars, expected in [(1, 2.4), (2, 2.7), (3, 3.0), (4, 3.3), (5, 3.6)]:
        service = ReviewService()
        service.submit_review("a", "b", stars)
        assert service.get_score("b") == expected


def test_recent_reviews_weigh_more():
    good_then_bad = ReviewService()
    bad_then_good = ReviewService()
    for stars in (5, 5, 5, 1):
        good_then_bad.submit_review("a", "x", stars)
    for stars in (1, 5, 5, 5):
        bad_then_good.submit_review("a", "x", stars)
    assert bad_then_good.get_score("x") > good_then_bad.get_score("x")


def test_review_count_and_summary():
    service = ReviewService()
    assert service.summary("new") == {"score": 3.0, "count": 0}
    service.submit_review("a", "new", 5)
    service.submit_review("b", "new", 4)
    # 3.0 -> 3.6 -> 0.3*4 + 0.7*3.6 = 3.72
    assert service.summary("new") == {"score": 3.7, "count": 2}


def test_bool_is_not_a_star_rating():
    service = ReviewService()
    with pytest.raises(ValueError):
        service.submit_review("a", "b", True)
