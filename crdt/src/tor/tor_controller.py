import logging
from time import sleep

from stem import SocketError
from stem.control import Controller

class TorController(object):
    def __init__(self, port, key):
        self.port = port
        self.key = key

    def connect(self):
        while True:
            try:
                with Controller.from_port() as controller:
                    controller.authenticate()
                    basic_auth = {}
                    logging.debug('Starting Tor hidden service')
                    response = controller.create_ephemeral_hidden_service(
                        {self.port: self.port}, key_type='RSA1024', key_content=self.key, await_publication=True,
                        detached=True
                    )
                    self.onion_addr = response.service_id
                    logging.debug('Tor hidden service running at {}.onion'.format(self.onion_addr))
                    return
            except SocketError as e:
                logging.error('Couldn\'t connect to tor control retrying in 5s: {}'.format(e))
                sleep(5)

    def disconnect(self):
        with Controller.from_port() as controller:
            controller.authenticate()
            controller.remove_ephemeral_hidden_service(self.onion_addr)

    def set_client_auth(self):
        pass
