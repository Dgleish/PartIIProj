import json

import plotly as py

with open('relays', 'r') as f:
    relays = f.readlines()
lats = []
longs = []
for r in relays:
    r = r.split(':::')[:-1]
    lats.append([json.loads(node)['latitude'] for node in r])
    longs.append([json.loads(node)['longitude'] for node in r])
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
            )
        )
    )
layout = dict(
    title='Tor relays',
)
fig = dict(data=data, layout=layout)
py.offline.plot(fig, filename='TorRelays')
