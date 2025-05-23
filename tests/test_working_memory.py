import pytest
from greeum.working_memory import STMWorkingSet


def test_add_and_get_recent():
    wm = STMWorkingSet(capacity=3, ttl_seconds=60)
    wm.add("a")
    wm.add("b")
    wm.add("c")
    recent = [slot.content for slot in wm.get_recent()]
    assert recent == ["c", "b", "a"]


def test_capacity_trim():
    wm = STMWorkingSet(capacity=2, ttl_seconds=60)
    wm.add("x")
    wm.add("y")
    wm.add("z")  # should evict "x"
    recent = [slot.content for slot in wm.get_recent()]
    assert recent == ["z", "y"]


def test_ttl_expiry(monkeypatch):
    wm = STMWorkingSet(capacity=3, ttl_seconds=1)
    wm.add("m1")
    import time
    time.sleep(1.2)
    wm.add("m2")
    recent = [slot.content for slot in wm.get_recent()]
    assert recent == ["m2"] 