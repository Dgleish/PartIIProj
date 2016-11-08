from list_crdt import OrderedList
import pytest

@pytest.mark.parametrize("a,b", [
    ("3+5", 8),
    ("2+4", 6),
    ("6*9", 54),
])
def test_eval(a,b):
    assert eval(a) == b

@pytest.fixture(
    params=["a", "b"]
)
def o_list(request):
    from ordered_list import OrderedList
    return OrderedList(request.param)

def test_merge(o_list):
    assert 'a' == o_list.merge(1) or 'b' == o_list.merge(1)

def test_merge_insert(o_list):
    pass

def test_merge_delete():
    pass