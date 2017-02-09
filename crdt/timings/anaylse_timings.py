import plotly as py
import plotly.graph_objs as go

with open('zgniuhrecv', 'r') as f:
    recvdata1 = [l[:-2] for l in f.readlines()]

with open('zgniuh', 'r') as f:
    senddata = [l[:-2] for l in f.readlines()]

print(len(recvdata1))
print(len(senddata))

results1 = [float(recvdata1[i]) - float(senddata[i]) for i in range(len(recvdata1))]
x = range(len(recvdata1))
trace1 = go.Scatter(
    x=list(x),
    y=results1,
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
    title='time taken over Tor network',
)
fig = go.Figure(data=data, layout=layout)
avgtime1 = sum([float(recvdata1[i]) - float(senddata[i]) for i in range(len(recvdata1))]) / len(recvdata1)
py.offline.plot(fig, filename='' + 'tortiming')

print(avgtime1)
