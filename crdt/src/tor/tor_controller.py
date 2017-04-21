import logging
from time import sleep, process_time

from stem import SocketError
from stem.control import Controller


class TorController(object):
    def __init__(self, port, key, auth_cookies, my_cookie):
        self.port = port
        self.key = key
        self.auth_cookies = auth_cookies
        self.my_cookie = my_cookie

        # LENGTH_MEASUREMENT:
        self.start_time = 0

    def connect(self):
        """
        Start a Tor hidden service using the provided port and key
        """
        while True:
            try:
                with Controller.from_port() as controller:
                    controller.authenticate()
                    if self.auth_cookies is not None:
                        # set the HidServAuth parameter for this peer to connect to other HSes
                        controller.set_conf(
                            'HidServAuth', ['{}.onion {}'.format(addr, self.my_cookie) for addr in self.auth_cookies]
                        )
                        logging.debug('hidservauth set to {}'.format(controller.get_conf('HidServAuth', multiple=True)))

                        # specify what HidServAuths are required for connecting to this
                        basic_auth = {addr: cookie for addr, cookie in self.auth_cookies.items()}
                        logging.debug('setting basic auth {}'.format(basic_auth))

                        logging.debug('Starting Tor hidden service')
                        response = controller.create_ephemeral_hidden_service(
                            {self.port: self.port}, key_type='RSA1024', key_content=self.key, await_publication=True,
                            detached=True, basic_auth=basic_auth
                        )
                    else:
                        response = controller.create_ephemeral_hidden_service(
                            {self.port: self.port}, key_type='RSA1024', key_content=self.key, await_publication=True,
                            detached=True
                        )
                    self.onion_addr = response.service_id
                    logging.debug('Tor hidden service running at {}.onion'.format(self.onion_addr))
                    logging.debug('with basic auth {}'.format(response.client_auth))

                    # LENGTH_MEASUREMENT
                    self.start_time = process_time()

                    return
            except SocketError as e:
                logging.error('Couldn\'t connect to tor control retrying in 5s: {}'.format(e))
                sleep(5)

    def disconnect(self):
        """
        Destroy the Tor hidden service. If this isn't done, the next create call will fail!
        """
        with Controller.from_port() as controller:
            controller.authenticate()
            controller.remove_ephemeral_hidden_service(self.onion_addr)
            logging.debug('Time elapsed {}'.format(process_time() - self.start_time))

    def set_client_auth(self):
        pass
