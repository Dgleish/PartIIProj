from Crypto.PublicKey import RSA
from stem.control import Controller

num_keys = 30
with Controller.from_port() as controller:
    controller.authenticate('password')
    with open('../../keys', 'w') as f:
        for i in range(num_keys):
            key = RSA.generate(1024)
            key_to_write = key.exportKey('PEM').split('-----')[2].replace('\n', '')
            service = controller.create_ephemeral_hidden_service({80: 5000}, key_type='RSA1024',
                                                                 key_content=key_to_write,
                                                                 await_publication=True)
            # onion_address = hashlib.sha1(key.publickey().exportKey('DER')).digest()[:10]
            # onion = base64.b32encode(onion_address).decode('utf-8').lower()
            onion = service.service_id
            f.write(key_to_write + '\n' + onion + '\n')
            controller.remove_ephemeral_hidden_service(service.service_id)
            print('generated key {} of {}'.format(i + 1, num_keys))
