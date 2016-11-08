import pytest
from list_crdt import ListCRDT
from ll_ordered_list import LLOrderedList

@pytest.fixture(
    params=['A','B']
)
def list_crdt(request):
    return ListCRDT(request.param,LLOrderedList())

def test_insert(list_crdt):
    assert isinstance(list_crdt,ListCRDT)
    list_crdt.add_right(None, ('a','1:A'))
    list_crdt.add_right(None, ('b','2:A'))
    list_crdt.add_right(None, ('c','3:A'))
    list_crdt.add_right(None, ('d','1:B'))
    list_crdt.add_right(('a','1:A'), ('e','4:A'))
    list_crdt.delete(('b','2:A'))
    list_crdt.delete(('d', '1:B'))
    res = list_crdt.pretty_print()
    assert res == 'cae'