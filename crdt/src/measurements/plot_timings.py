import plotly as py
import plotly.graph_objs as go
from plotly import tools

from crdt.arr_ordered_list import ArrOrderedList
from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt.ll_ordered_list import LLOrderedList
from crdt_app import CRDTApp


def add_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp(127001, 8889, '127.0.0.1', ops_to_do=[CRDTOpAddRightLocal('1')] * 1000,
                      list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [min(sum(l[i]) for l in results) for i in range(len(results[0]))]
    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp(127001, 8889, '127.0.0.1', ops_to_do=[CRDTOpAddRightLocal('1')] * 1000,
                      list_repr=ArrOrderedList)
        results2.append(app.time())

    aggr2 = [min(sum(l[i]) for l in results2) for i in range(len(results2[0]))]
    double(aggr, 'LLOrderedList', aggr2, 'ArrOrderedList', 'add_right_local_cost',
           'Timing of AddRightLocal in two implementations')


def detail_add_olist_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp(127001, 8889, '127.0.0.1',
                      ops_to_do=[CRDTOpAddRightLocal('1')] * 10000, list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(5)]

    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app2 = CRDTApp(127001, 8889, '127.0.0.1',
                       ops_to_do=[CRDTOpAddRightLocal('1')] * 10000, list_repr=ArrOrderedList)
        results2.append(app2.time())
    aggr2 = [[min(sample[i][j] for sample in results2) for i in range(len(results2[0]))] for j in range(5)]
    double_stacked(aggr, 'LLOrderedList', aggr2, 'ArrOrderedList',
                   ['insertion', 'store_op', 'client_update', 'network_send', 'recovery'],
                   'add_right_local dual cost', 'Timing of AddRightLocal in two implementations')


def plotly_add_long():
    results = []
    for i in range(10):
        print('iteration {}'.format(i + 1))
        app = CRDTApp(127001, 8889, '127.0.0.1',
                      ops_to_do=[CRDTOpAddRightLocal('1')] * 10000, list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(5)]
    plotly_stacked(aggr, ['insertion', 'store_op', 'client_update', 'network_send', 'recovery'],
                   'Detailed timing of LLOrderedList over 10000 operations', 'add_local_ll_long')


def detail_remove_olist_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp(127001, 8889, '127.0.0.1',
                      ops_to_do=[CRDTOpDeleteLocal()] * 10000, list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(5)]

    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app2 = CRDTApp(127001, 8889, '127.0.0.1',
                       ops_to_do=[CRDTOpDeleteLocal()] * 10000, list_repr=ArrOrderedList)
        results2.append(app2.time())
    aggr2 = [[min(sample[i][j] for sample in results2) for i in range(len(results2[0]))] for j in range(5)]
    double_stacked(aggr, 'LLOrderedList', aggr2, 'ArrOrderedList',
                   ['insertion', 'store_op', 'client_update', 'network_send', 'recovery'],
                   'delete_local detail cost', 'Timing of DeleteLocal in two implementations')


def double(results1, title1, results2, title2, filename, title):
    x = range(len(results1))
    trace1 = go.Scatter(
        x=list(x),
        y=results1,
        mode='lines',
        line=dict(width=0.5),
        name=title1
    )
    trace2 = go.Scatter(
        x=list(x),
        y=results2,
        mode='lines',
        line=dict(width=0.5),
        name=title2
    )
    data = [trace1, trace2]
    layout = go.Layout(
        xaxis=dict(
            type='linear',
            title='Operation no.'
        ),
        yaxis=dict(
            type='linear',
            title='Time taken (s)'
        ),
        title=title,
    )
    fig = go.Figure(data=data, layout=layout)
    py.offline.plot(fig, filename='images/' + filename)


def double_stacked(results1, title1, results2, title2, labels, filename, title):
    data1 = gen_stacked_data(results1, labels, 1)
    data2 = gen_stacked_data(results2, labels, 2)

    fig = tools.make_subplots(rows=2, cols=1, subplot_titles=(title1, title2))
    for trace in data1:
        fig.append_trace(trace, 1, 1)

    for trace in data2:
        fig.append_trace(trace, 2, 1)

    fig['layout'].update(
        title=title,
        xaxis1=dict(
            title='Operation no.'
        ),
        yaxis1=dict(
            title='Time taken (s)'
        ),
        xaxis2=dict(
            title='Operation no.'
        ),
        yaxis2=dict(
            title='Time taken (s)'
        ),
        legend=dict(x=0.45, y=0.55, orientation='h')

    )
    py.offline.plot(fig, filename='images/' + filename)


def gen_stacked_data(aggr_results, labels, group):
    x = range(len(aggr_results[0]))
    return [go.Scatter(
        x=list(x),
        y=[sum([l[k] for l in aggr_results[:i + 1]]) for k in range(len(aggr_results[0]))],
        mode='lines',
        line=dict(width=0.5),
        fill='tonexty',
        name=labels[i],
        legendgroup='group%d' % group,
    ) for i in range(len(aggr_results))]


def plotly_stacked(aggr_results, labels, title, filename):
    data = gen_stacked_data(aggr_results, labels, 1)
    layout = go.Layout(
        xaxis=dict(
            type='linear',
            title='Operation no.'
        ),
        yaxis=dict(
            type='linear',
            title='Time taken (s)'
        ),
        title=title,
    )
    fig = go.Figure(data=data, layout=layout)
    py.offline.plot(fig, filename='images/' + filename)


if __name__ == '__main__':
    add_time(10)
