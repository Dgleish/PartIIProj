import json
import logging

import plotly as py
import plotly.graph_objs as go
import requests
from stem import CircStatus
from stem.control import Controller

from crdt.ops import OpAddRightLocal
from crdt.ordered_list.ll_ordered_list import LLOrderedList
from crdt_app import CRDTApp

url = 'http://freegeoip.net/json/'


def time_latency(num, iterations):
    results = []
    for i in range(iterations):
        app = CRDTApp('alex', 8889, '26ny4uuqnztxvdrx', ops_to_do=[OpAddRightLocal('1')] * 100,
                      priv_key='MIICXAIBAAKBgQDZV3gtx3ZLFZKZXU8skVXZmAWaNqWgz6/XkL7934XxnyNZr2kvg7Rd+yKmlGoz6/AEDa6/a7afupi7KWunfQpK2n3WyaUEZXIt+Ec/YYUJENrjcvODtd4vf40POeH6zz1o8Lbomn060g8/PkeCmIbYvqP02ozr5UUl93yW67/f4QIDAQABAoGAFmgeozWXm/kO4pHMmk8ndyXlmfb9T11qBwLMtfan4/egmNvtL7FX1IKSGXNemZi+52QTundb3g7KNS15hExvVYR7Bk9zrcu7THrjQFH3kS6Vk8gHca5SEMJt0RaMuD1fm7Y1P/78ZPpA5Ov/W0p0ubhKY530pwEbPOmAdTaEFRkCQQDbjec16kJ3gY67ND717VoT0UJ/v55teEna/B5CWiNNNYbvDHtUnfFDBqm5SdOpnSgsDydEIO0iQNUIjPrzSLStAkEA/WuKA+up1cz/eH67fboU3g2cuKethLpGFzKiQbTcyjwhD748PC06MF8ixoKbhaLsrv6EoylUiJ673gEbJcBKhQJAQmYMArYyG8pGzD7ku6Nolo22usPMufai/2M4E4EHJBaIFEuGEPUjPc4KDktRg/5PY+PBUE1U6gMJamiYjHL0kQJAPOr+8FZUKyruNn7wfxaeMYrAI7tbAM7uTmFDk9vwP0UZBXnLbQPKOxqDd4ip7gPuNVrFc5tZ0MWnj4RgjECfKQJBANDFieHrQ9knsCOFK9em43Xo+cHyFp61OUllmBY/4seOwN1jFTLw2+i8gh8uOQm94wtvz5hvBPzr5qdIRdh50Uw=',
                      known_peers=['26ny4uuqnztxvdrx'], list_repr=LLOrderedList)

        with open('recv' + str(num), 'r') as f:
            recvdata1 = [l[:-2] for l in f.readlines()]

        with open('send' + str(num), 'r') as f:
            senddata = [l[:-2] for l in f.readlines()]

        print(len(recvdata1))
        print(len(senddata))
        avgtime1 = sum([float(recvdata1[i]) - float(senddata[i]) for i in range(len(recvdata1))]) / len(recvdata1)
        print(avgtime1)
        curr_result = [float(recvdata1[i]) - float(senddata[i]) for i in range(len(recvdata1))]
        results.append(curr_result)
    x = range(len(results[0]))

    trace1 = go.Scatter(
        x=list(x),
        y=[min(results[i][j] for i in range(iterations)) for j in range(len(results[0]))],
        mode='markers',
        name='trace 1'
    )
    data = [trace1]
    layout = go.Layout(
        xaxis=dict(
            type='linear',
            title='Operation no.'
        ),
        yaxis=dict(
            type='linear',
            title='Time taken (s)'
        ),
        title='Time taken over Tor network',
    )
    fig = go.Figure(data=data, layout=layout)
    py.offline.plot(fig, filename='' + 'tortiming' + str(num))


def print_circuits(num):
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()

        print('Hidden services running %s ' % controller.list_ephemeral_hidden_services(detached=True))
        print('CIRCUITS')
        print(controller.get_streams())
        with open('relays' + str(num), 'w+') as f:
            for circ in controller.get_circuits():
                if circ.status != CircStatus.BUILT:
                    continue
                if circ.purpose == 'HS_CLIENT_REND' or circ.purpose == 'HS_SERVICE_REND':
                    # f.write('|{}|{}|{}|{}|'.format(circ.id, circ.hs_state, circ.rend_query, circ.build_flags))
                    print("CIRCUIT %s (%s)" % (circ.id, circ.purpose))
                    print("Hidden service: %s\n"
                          "Rendez-vous point: %s\n"
                          "Flags: %s" % (circ.hs_state, circ.rend_query, circ.build_flags))
                    for i, (fp, nickname) in enumerate(circ.path):
                        # fp is fingerprint (UID)
                        desc = controller.get_network_status(fp, None)
                        address = desc.address if desc else 'unknown'
                        results = requests.get(url + address)
                        f.write(nickname + '::' + json.dumps(results.json()) + ':::')
                        print("Relay %d: %s" % (i, fp))
                        print("  nickname: %s" % nickname)
                        print("  address: %s" % address)
                    print()
                    f.write('\n')


def plot_locs(num):
    with open('relays' + str(num), 'r') as f:
        circuits = f.readlines()
    lats = []
    longs = []
    for r in circuits:
        r = r.split('|')[-1].split(':::')[:-1]
        logging.debug('relay: {}'.format(r))
        lats.append([52.2042330] + [json.loads(node.split('::')[1])['latitude'] for node in r])
        longs.append([0.1055130] + [json.loads(node.split('::')[1])['longitude'] for node in r])
    data = []
    for i, d in enumerate(lats):
        data.append(
            dict(
                type='scattergeo',
                lat=d,
                lon=longs[i],
                mode='lines',
                line=dict(
                    width=1

                ),
                name='Circuit {}'.format(i + 1),
            )
        )

    layout = dict(
        title='Tor relays',
    )
    fig = dict(data=data, layout=layout)
    py.offline.plot(fig, filename='TorRelays' + str(num))


if __name__ == '__main__':
    time_latency(11, 15)
    print_circuits(11)
    plot_locs(11)
