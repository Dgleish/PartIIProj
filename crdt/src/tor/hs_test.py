import socket
import threading
from time import sleep

import socks
from stem.control import Controller


def createHS(port, key):
    with Controller.from_port() as controller:
        controller.authenticate('password')
    basic_auth = {}
    print('Starting Tor hidden service')
    response = controller.create_ephemeral_hidden_service(
        {port: port}, key_type='RSA1024', key_content=key, await_publication=True
    )
    onion_addr = response.service_id
    print('Tor hidden service running at {}.onion'.format(onion_addr))


def client(onion, port):
    socks.set_default_proxy(socks.SOCKS5, "localhost", port=9050)
    sock = socks.socksocket()
    print('connecting to {} over Tor'.format(onion + '.onion'))
    sock.connect((onion + '.onion', port))
    sleep(10)


def server(port):
    recvsock = socket.socket()
    recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    recvsock.bind(('', port))
    recvsock.listen(100)
    while True:
        print('listening')
        sock, addr = recvsock.accept()
        print('peer connected from {}'.format(addr))


if __name__ == '__main__':
    key = "MIICXAIBAAKBgQDZV3gtx3ZLFZKZXU8skVXZmAWaNqWgz6/XkL7934XxnyNZr2kvg7Rd+yKmlGoz6/AEDa6/a7afupi7KWunfQpK2n3WyaUEZXIt+Ec/YYUJENrjcvODtd4vf40POeH6zz1o8Lbomn060g8/PkeCmIbYvqP02ozr5UUl93yW67/f4QIDAQABAoGAFmgeozWXm/kO4pHMmk8ndyXlmfb9T11qBwLMtfan4/egmNvtL7FX1IKSGXNemZi+52QTundb3g7KNS15hExvVYR7Bk9zrcu7THrjQFH3kS6Vk8gHca5SEMJt0RaMuD1fm7Y1P/78ZPpA5Ov/W0p0ubhKY530pwEbPOmAdTaEFRkCQQDbjec16kJ3gY67ND717VoT0UJ/v55teEna/B5CWiNNNYbvDHtUnfFDBqm5SdOpnSgsDydEIO0iQNUIjPrzSLStAkEA/WuKA+up1cz/eH67fboU3g2cuKethLpGFzKiQbTcyjwhD748PC06MF8ixoKbhaLsrv6EoylUiJ673gEbJcBKhQJAQmYMArYyG8pGzD7ku6Nolo22usPMufai/2M4E4EHJBaIFEuGEPUjPc4KDktRg/5PY+PBUE1U6gMJamiYjHL0kQJAPOr+8FZUKyruNn7wfxaeMYrAI7tbAM7uTmFDk9vwP0UZBXnLbQPKOxqDd4ip7gPuNVrFc5tZ0MWnj4RgjECfKQJBANDFieHrQ9knsCOFK9em43Xo+cHyFp61OUllmBY/4seOwN1jFTLw2+i8gh8uOQm94wtvz5hvBPzr5qdIRdh50Uw="
    onion = "26ny4uuqnztxvdrx"
    port = 8889
    sv = threading.Thread(target=server, args=(port,))
    sv.daemon = True
    sv.start()
    print('creating hidden service')
    createHS(port, key)
    client(onion, port)
