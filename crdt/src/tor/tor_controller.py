import logging

from stem.control import Controller


class TorController(object):
    def __init__(self, port, key):
        self.port = port
        self.key = key

    def connect(self):
        with Controller.from_port() as controller:
            try:
                controller.authenticate()
                basic_auth = {}
                logging.debug('Starting Tor hidden service')
                response = controller.create_ephemeral_hidden_service(
                    {self.port: self.port}, key_type='RSA1024', key_content=self.key, await_publication=True,
                    detached=True
                )
                self.onion_addr = response.service_id
                logging.debug('Tor hidden service runnning at {}.onion'.format(self.onion_addr))
            except Exception as e:
                logging.error('Exception: {}'.format(e))

    def disconnect(self):
        with Controller.from_port() as controller:
            controller.authenticate()
            controller.remove_ephemeral_hidden_service(self.onion_addr)

    def set_client_auth(self):
        pass
