from tools.connected_peers import ConnectedPeers


def test_connected_peers1():
    c = ConnectedPeers()
    c.add_peer('1', None, 'E')
    c.add_peer('2', None, 'E2')
    c.remove_all()
    assert c.is_empty()


def test_connected_peers2():
    c = ConnectedPeers()
    c.add_peer('1', None, 'E')
    c.remove_peer('1')
    assert c.is_empty()


def test_connected_peers3():
    c = ConnectedPeers()
    c.add_peer('1', None, 'c')
    a = c.get_cipher_for_peer('1')
    assert a == 'c'


def test_connected_peers4():
    c = ConnectedPeers()
    c.add_peer('1', None, 'e')
    sock = c.get_sock_for_peer('1')
    assert sock is None


def test_connected_peers5():
    c = ConnectedPeers()
    count = 0
    c.add_peer('1', None, 'E')
    c.add_peer('2', None, 'E')
    c.add_peer('3', None, 'E2')
    c.add_peer('4', None, 'E2')
    for _ in c.iterate():
        count += 1
    assert count == 4


def test_connected_peers6():
    c = ConnectedPeers()
    count = 0
    c.add_peer('1', None, 'E')
    c.add_peer('2', None, 'E')
    c.add_peer('3', None, 'E2')
    c.add_peer('4', None, 'E2')
    for _ in c.iterate_sockets():
        count += 1
    assert count == 4
