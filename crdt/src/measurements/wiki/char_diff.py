import logging

import plotly as py
import plotly.graph_objs as go
import requests
from simplediff import diff

from crdt.list_crdt import ListCRDT
from crdt.ops import OpAddRightLocal, OpDeleteLocal, CRDTOpDeleteRemote, OpAddRightRemote
from crdt.ops import RemoteOp
from crdt.ordered_list.ll_ordered_list import LLOrderedList
from crdt.ordered_list.lseq_ordered_list import LSEQOrderedList


def scrape(title):
    url = 'https://en.wikipedia.org/w/api.php?action=query&titles={}&prop=revisions&rvprop' \
          '=content&format=json&rvlimit=200'.format(title)

    result = requests.get(url).json()["query"]["pages"]
    for x in result:
        result = [r['*'] for r in result[x]["revisions"]]
    result.reverse()
    return result


def build_initial_state(chars, ol):
    list_crdt = ListCRDT('A', ol('A'))
    ops = []
    for l in chars:
        op, _ = list_crdt.perform_op(OpAddRightLocal(l))
        assert isinstance(op, RemoteOp)
        ops.append(op)

    return list_crdt, ops


def parse(revisions, ol):
    crdt, ops = build_initial_state(revisions[0], ol)
    prev = revisions[0]
    i = 0
    for edit in revisions[1:]:
        print(i, len(revisions) - 1)
        i += 1
        crdt.reset_cursor()
        char_diff_list = diff(prev, edit)
        print('diff length {}'.format(len(char_diff_list)))
        for type, chars in char_diff_list:
            # type is '-', '+' or '='
            if type == '=':
                for c in chars:
                    crdt.move_cursor('Right')

            elif type == '-':
                for c in chars:
                    crdt.move_cursor('Right')
                    op, _ = crdt.perform_op(OpDeleteLocal())
                    ops.append(op)

            elif type == '+':
                for c in chars:
                    op, _ = crdt.perform_op(OpAddRightLocal(c))
                    ops.append(op)

            else:
                logging.warning('unexpected diff type')

        prev = edit
    return ops


def plot_ids(tree_ids, ll_ops, filename):
    cum_length = 0
    tree_lengths = []
    for i, tree_op in enumerate(tree_ids):
        if isinstance(tree_op, OpAddRightRemote):
            cum_length += tree_op.vertex_to_add[1].get_num_bits() / 8
        elif isinstance(tree_op, CRDTOpDeleteRemote):
            cum_length -= tree_op.vertex_id.get_num_bits() / 8
        tree_lengths.append(cum_length)

    cum_length = 0
    ll_lengths = []
    for i, ll_op in enumerate(ll_ops):
        if isinstance(ll_op, OpAddRightRemote):
            cum_length += len(ll_op.vertex_to_add[1].value)
        ll_lengths.append(cum_length)

    data = \
        [
            go.Scatter(
                x=list(range(len(ll_lengths))),
                y=ll_lengths,
                name='RGA'
            ),
            go.Scatter(
                x=list(range(len(tree_lengths))),
                y=tree_lengths,
                name='LSEQ'
            )
        ]
    layout = go.Layout(
        xaxis=dict(
            type='linear',
            title='Operation number'
        ),
        yaxis=dict(
            type='linear',
            title='Total memory used by identifiers (bytes)'
        ),
    )
    fig = go.Figure(data=data, layout=layout)
    py.offline.plot(fig, filename='{}.html'.format(filename))


if __name__ == '__main__':
    revisions = scrape('Sehna')
    lseq_ops = parse(revisions, LSEQOrderedList)
    ll_ops = parse(revisions, LLOrderedList)
    plot_ids(lseq_ops, ll_ops, 'Sehna')

    revisions = scrape('Oxbridge')
    lseq_ops = parse(revisions, LSEQOrderedList)
    ll_ops = parse(revisions, LLOrderedList)
    plot_ids(lseq_ops, ll_ops, 'Oxbridge')

    revisions = scrape('Wikipedia:Administrator_intervention_against_vandalism')
    lseq_ops = parse(revisions, LSEQOrderedList)
    ll_ops = parse(revisions, LLOrderedList)
    plot_ids(lseq_ops, ll_ops, 'Administrator_intervention')

    # parse([
    #     'a',
    #     'abcd',
    #     'bce',
    #     'abced',
    #     'abcde'
    # ])
