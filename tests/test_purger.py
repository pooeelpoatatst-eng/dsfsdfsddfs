from app.modules.purger import MAX_DELETE, _limit


def test_delete_limits_are_bounded() -> None:
    assert _limit([]) == 25
    assert _limit(["100"]) == MAX_DELETE
    assert _limit(["101"]) is None
