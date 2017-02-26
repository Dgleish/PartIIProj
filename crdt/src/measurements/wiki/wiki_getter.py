import difflib

import plotly as py
import plotly.graph_objs as go
import requests

from crdt.crdt_ops import CRDTOpAddRightRemote, CRDTOpDeleteRemote
from crdt.ordered_list.ll_ordered_list import LLOrderedList
from crdt.ordered_list.lseq_ordered_list import LSEQOrderedList
from measurements.wiki import parse_diff


def patchify(first, revisions):
    prev = first
    patch = -1
    patches = []
    for i, rev in enumerate(revisions[1:]):
        content = rev["*"].split('\n')
        with open("file{}".format(i), "w+") as f:
            f.write(rev["*"])
        diff = difflib.unified_diff(prev, content, n=1)
        for d in list(diff)[2:]:
            if d[:2] == '@@':
                patch += 1
                patches.append([d])
            else:
                patches[patch].append(d)
        prev = content
    return first, patches


def scrape(title):
    url = 'https://en.wikipedia.org/w/api.php?action=query&titles={}&prop=revisions&rvprop' \
          '=content&format=json&rvlimit=500'.format(title)

    result = requests.get(url).json()["query"]["pages"]
    for x in result:
        result = result[x]["revisions"]
    first = result[0]["*"].split('\n')
    with open("orig", "w+") as f:
        f.write(result[0]["*"])

    return patchify(first, result)


def plot_ids(tree_ids, ll_ops):
    cum_length = 0
    tree_lengths = []
    for i, tree_op in enumerate(tree_ids):
        if isinstance(tree_op, CRDTOpAddRightRemote):
            cum_length += tree_op.vertex_to_add[1].get_num_bits() / 8
        elif isinstance(tree_op, CRDTOpDeleteRemote):
            cum_length -= tree_op.vertex_id.get_num_bits() / 8
        tree_lengths.append(cum_length)

    cum_length = 0
    ll_lengths = []
    for i, ll_op in enumerate(ll_ops):
        if isinstance(ll_op, CRDTOpAddRightRemote):
            cum_length += len(ll_op.vertex_to_add[1].value)
        ll_lengths.append(cum_length)

    data = [go.Scatter(
        x=list(range(len(tree_lengths))),
        y=tree_lengths,
        mode='lines'
    ),
        go.Scatter(
            x=list(range(len(ll_lengths))),
            y=ll_lengths
        )]
    layout = go.Layout(
        xaxis=dict(
            type='linear',
            title='Operation no.'
        ),
        yaxis=dict(
            type='linear',
            title='Cumulative ID memory used (bytes)'
        ),
        title='inserted ids over time',
    )
    fig = go.Figure(data=data, layout=layout)
    py.offline.plot(fig, filename='tree_ids.html')


if __name__ == '__main__':
    first, patches = scrape('Wikipedia:Administrator_intervention_against_vandalism')
    # first, patches = scrape('United_Nations')

    # print(patches)
    diff_vertex_ids, list_crdt = parse_diff.parse_diff(first, patches, LSEQOrderedList)
    print(len(list_crdt))

    diff_vertex_ids2, list_crdt2 = parse_diff.parse_diff(first, patches, LLOrderedList)

    print(len(list_crdt2))

    plot_ids(diff_vertex_ids, diff_vertex_ids2)
