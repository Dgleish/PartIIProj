import json

import requests
from stem import CircStatus
from stem.control import Controller

url = 'http://freegeoip.net/json/'


def print_circuits():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()

        print('Hidden services running %s ' % controller.list_ephemeral_hidden_services(detached=True))
        print('CIRCUITS')
        print(controller.get_streams())
        with open('relays', 'w') as f:
            for circ in controller.get_circuits():
                if circ.status != CircStatus.BUILT:
                    continue
                f.write('{}|{}|{}|{}'.format(circ.id, circ.hs_state, circ.rend_query, circ.build_flags))
                print("CIRCUIT %s" % circ.id)
                print("Hidden service: %s\n"
                      "Rendez-vous point: %s\n"
                      "Flags: %s" % (circ.hs_state, circ.rend_query, circ.build_flags))
                for i, (fp, nickname) in enumerate(circ.path):
                    # fp is fingerprint (UID)
                    desc = controller.get_network_status(fp, None)
                    address = desc.address if desc else 'unknown'
                    results = requests.get(url + address)
                    f.write(nickname + json.dumps(results.json()) + ':::')
                    print("Relay %d: %s" % (i, fp))
                    print("  nickname: %s" % nickname)
                    print("  address: %s" % address)
                print()
                f.write('\n')


if __name__ == '__main__':
    print_circuits()
