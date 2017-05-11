import plotly as py
import plotly.graph_objs as go
from plotly import tools

from crdt.ops import OpAddRightLocal, OpDeleteLocal
from crdt.ordered_list.arr_ordered_list import ArrOrderedList
from crdt.ordered_list.ll_ordered_list import LLOrderedList
from crdt.ordered_list.lseq_ordered_list import LSEQOrderedList
from crdt_app import CRDTApp


def add_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp('127001', 8889, '127.0.0.1', ops_to_do=[OpAddRightLocal('1')] * 10000,
                      list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [min(sum(l[i][:2] + l[i][3:]) for l in results) for i in range(len(results[0]))]

    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app2 = CRDTApp('127001', 8889, '127.0.0.1', ops_to_do=[OpAddRightLocal('1')] * 10000,
                       list_repr=ArrOrderedList)
        results2.append(app2.time())
    aggr2 = [min(sum(l[i][:2] + l[i][3:]) for l in results2) for i in range(len(results2[0]))]

    results3 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app3 = CRDTApp('127001', 8889, '127.0.0.1', ops_to_do=[OpAddRightLocal('1')] * 10000,
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
                      ops_to_do=[OpAddRightLocal('1')] * 50000, list_repr=LLOrderedList)
        results.append(app.time())
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(4)]

    # results2 = []
    # for i in range(iterations):
    #     print('iteration {}'.format(i + 1))
    #     app2 = CRDTApp('127001', 8889, '127.0.0.1',
    #                    ops_to_do=[CRDTOpAddRightLocal('1')] * 50000, list_repr=LSEQOrderedList)
    #     results2.append(app2.time())
    # aggr2 = [[min(sample[i][j] for sample in results2) for i in range(len(results2[0]))] for j in range(4)]

    # results3 = []
    # for i in range(iterations):
    #     print('iteration {}'.format(i + 1))
    #     app3 = CRDTApp('127001', 8889, '127.0.0.1',
    #                    ops_to_do=[CRDTOpAddRightLocal('1')] * 50000, list_repr=ArrOrderedList)
    #     results3.append(app3.time())
    # aggr3 = [[min(sample[i][j] for sample in results3) for i in range(len(results3[0]))] for j in range(4)]

    stacked([aggr], ['LLOrderedList'],
            ['insertion', 'store_op', 'network_send', 'recovery'],
            'add_LL', 'Latency of AddRightLocal for LLOrderedList')
    # stacked([aggr2], ['LSEQOrderedList'],
    #         ['insertion', 'store_op', 'network_send', 'recovery'],
    #         'add_LSEQ', 'Latency of AddRightLocal for LSEQOrderedList')
    # stacked([aggr3], ['ArrOrderedList'],
    #         ['insertion', 'store_op', 'network_send', 'recovery'],
    #         'add_Arr', 'Latency of AddRightLocal for ArrOrderedList')


def detail_remove_olist_time(iterations):
    results = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app = CRDTApp('127001', 8889, '127.0.0.1',
                      ops_to_do=[OpDeleteLocal()] * 10000, list_repr=LLOrderedList)
        curr_result = app.time()
        curr_result.reverse()
        results.append(curr_result)
    aggr = [[min(sample[i][j] for sample in results) for i in range(len(results[0]))] for j in range(4)]


    results2 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app2 = CRDTApp('127001', 8889, '127.0.0.1',
                       ops_to_do=[OpDeleteLocal()] * 10000, list_repr=LSEQOrderedList)
        curr_result = app2.time()
        curr_result.reverse()
        results2.append(curr_result)
    aggr2 = [[min(sample[i][j] for sample in results2) for i in range(len(results2[0]))] for j in range(4)]

    results3 = []
    for i in range(iterations):
        print('iteration {}'.format(i + 1))
        app3 = CRDTApp('127001', 8889, '127.0.0.1',
                       ops_to_do=[OpDeleteLocal()] * 10000, list_repr=ArrOrderedList)
        curr_result = app3.time()
        curr_result.reverse()
        results3.append(curr_result)
    aggr3 = [[min(sample[i][j] for sample in results3) for i in range(len(results3[0]))] for j in range(4)]

    stacked([aggr], ['LLOrderedList'],
            ['deletion', 'store_op', 'network_send', 'recovery'],
            'delete_local LL', 'Latency of DeleteLocal for LLOrderedList')
    stacked([aggr2], ['LSEQOrderedList'],
            ['deletion', 'store_op', 'network_send', 'recovery'],
            'delete_local LSEQ', 'Latency of DeleteLocal for LSEQOrderedList')
    stacked([aggr3], ['ArrOrderedList'],
            ['deletion', 'store_op', 'network_send', 'recovery'],
            'delete_local Arr', 'Latency of DeleteLocal for ArrOrderedList')


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
        print('new data is {}'.format(new_data))
        datas.append(new_data)
        for trace in new_data:
            fig.append_trace(trace, i + 1, 1)

        axes['xaxis{}'.format(i + 1)] = dict(
            title='Document length',
        )
        axes['yaxis{}'.format(i + 1)] = dict(
            title='Time taken (s)'
        )

    fig['layout'].update(
        title=title,
    )
    fig['layout'].update(axes)
    py.offline.plot(fig, filename='../images/' + filename)


def subplot_test():
    fig = tools.make_subplots(rows=2, cols=1, subplot_titles=('', ''))
    fig.append_trace(go.Scatter(
        x=list(range(5)),
        y=[1, 2, 3, 4, 5],
        mode='lines',
        fill='tonexty'
    ), 1, 1)

    fig.append_trace(go.Scatter(
        x=list(range(5)),
        y=[0, 1, 2, 3, 4],
        mode='lines',
        fill='tonexty'
    ), 2, 1)
    py.offline.plot(fig, filename='test')


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
    ) for i in range(len(aggr_results))] \
           + [
               go.Scatter(
                   x=[],
                   y=[]
               )
           ]


def plotly_stacked(aggr_results, labels, title, filename):
    data = gen_stacked_data(aggr_results, labels, 1)
    layout = go.Layout(
        xaxis=dict(
            type='linear',
            title='Document length'
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
    detail_remove_olist_time(15)
    # detail_add_olist_time(15)
    # stacked([[[0,1,2],[0,1,2]],[[0,4,5],[0,4,5]]],['a','b'],['1','2'],'test','blah')
    # subplot_test()
