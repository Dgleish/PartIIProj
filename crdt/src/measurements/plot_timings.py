import plotly as py
import plotly.graph_objs as go
from plotly import tools

from crdt.arr_ordered_list import ArrOrderedList
from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal
from crdt.ll_ordered_list import LLOrderedList
from crdt.lseq_ordered_list import LSEQOrderedList
from crdt_app import CRDTApp


def add_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp('127001', 8889, '127.0.0.1', ops_to_do=[CRDTOpAddRightLocal('1')] * 10000,
                      list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [min(sum(l[i][:2] + l[i][3:]) for l in results) for i in range(len(results[0]))]

    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app2 = CRDTApp('127001', 8889, '127.0.0.1', ops_to_do=[CRDTOpAddRightLocal('1')] * 10000,
                       list_repr=ArrOrderedList)
        results2.append(app2.time())
    aggr2 = [min(sum(l[i][:2] + l[i][3:]) for l in results2) for i in range(len(results2[0]))]

    results3 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app3 = CRDTApp('127001', 8889, '127.0.0.1', ops_to_do=[CRDTOpAddRightLocal('1')] * 10000,
                       list_repr=LSEQOrderedList)
        results3.append(app3.time())
    aggr3 = [min(sum(l[i][:2] + l[i][3:]) for l in results3) for i in range(len(results3[0]))]

    double([aggr, aggr2, aggr3], ['LLOrderedList', 'ArrOrderedList', 'LSEQOrderedList'], 'add_right_local_cost',
           'Timing of AddRightLocal in different implementations')


def detail_add_olist_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp('127001', 8889, '127.0.0.1',
                      ops_to_do=[CRDTOpAddRightLocal('1')] * 10000, list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(5)]

    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app2 = CRDTApp('127001', 8889, '127.0.0.1',
                       ops_to_do=[CRDTOpAddRightLocal('1')] * 10000, list_repr=ArrOrderedList)
        results2.append(app2.time())
    aggr2 = [[min(sample[i][j] for sample in results2) for i in range(len(results2[0]))] for j in range(5)]

    results3 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app3 = CRDTApp('127001', 8889, '127.0.0.1',
                       ops_to_do=[CRDTOpAddRightLocal('1')] * 10000, list_repr=LSEQOrderedList)
        results3.append(app3.time())
    aggr3 = [[min(sample[i][j] for sample in results3) for i in range(len(results3[0]))] for j in range(5)]

    stacked([aggr, aggr2, aggr3], ['LLOrderedList', 'ArrOrderedList', 'LSEQOrderedList'],
            ['insertion', 'store_op', 'client_update', 'network_send', 'recovery'],
            'add_right_local_dual_cost', 'Timing of AddRightLocal in different implementations')


def plotly_add_long():
    results = []
    for i in range(10):
        print('iteration {}'.format(i + 1))
        app = CRDTApp('127001', 8889, '127.0.0.1',
                      ops_to_do=[CRDTOpAddRightLocal('1')] * 10000, list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(5)]
    plotly_stacked(aggr, ['insertion', 'store_op', 'client_update', 'network_send', 'recovery'],
                   'Detailed timing of LLOrderedList over 10000 operations', 'add_local_ll_long')


def detail_remove_olist_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp('127001', 8889, '127.0.0.1',
                      ops_to_do=[CRDTOpDeleteLocal()] * 10000, list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(5)]

    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app2 = CRDTApp('127001', 8889, '127.0.0.1',
                       ops_to_do=[CRDTOpDeleteLocal()] * 10000, list_repr=ArrOrderedList)
        results2.append(app2.time())
    aggr2 = [[min(sample[i][j] for sample in results2) for i in range(len(results2[0]))] for j in range(5)]

    results3 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app3 = CRDTApp('127001', 8889, '127.0.0.1',
                       ops_to_do=[CRDTOpDeleteLocal()] * 10000, list_repr=LSEQOrderedList)
        results3.append(app3.time())
    aggr3 = [[min(sample[i][j] for sample in results3) for i in range(len(results3[0]))] for j in range(5)]

    stacked([aggr, aggr2, aggr3], ['LLOrderedList', 'ArrOrderedList', 'LSEQOrderedList'],
            ['insertion', 'store_op', 'client_update', 'network_send', 'recovery'],
                   'delete_local detail cost', 'Timing of DeleteLocal in two implementations')


def double(results, titles, filename, title):
    x = range(len(results[0]))
    data = [
        go.Scatter(
            x=list(x),
            y=results[i],
            mode='lines',
            line=dict(width=0.5),
            name=titles[i]
        ) for i in range(len(results))
        ]
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
    py.offline.plot(fig, filename='../images/' + filename)


def stacked(results, titles, labels, filename, title):
    fig = tools.make_subplots(rows=len(results), cols=1, subplot_titles=tuple(titles))

    datas = []
    axes = {}
    for i, result in enumerate(results):
        new_data = gen_stacked_data(results[i], labels, i + 1)
        print('num_lines {}'.format(len(new_data)))
        datas.append(new_data)
        for trace in new_data:
            print('appending trace {}'.format(trace))
            fig.append_trace(trace, i + 1, 1)

        axes['xaxis{}'.format(i + 1)] = dict(
            title='Operation no.'
        )
        axes['yaxis{}'.format(i + 1)] = dict(
            title='Time taken (s)'
        )

    fig['layout'].update(
        title=title,
    )
    fig['layout'].update(axes)
    py.offline.plot(fig, filename='../images/' + filename)


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
    py.offline.plot(fig, filename='../images/' + filename)


if __name__ == '__main__':
    add_time(10)
