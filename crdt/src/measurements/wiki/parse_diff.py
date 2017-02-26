import re

from crdt.crdt_ops import CRDTOpAddRightLocal, RemoteCRDTOp, CRDTOpDeleteLocal
from crdt.list_crdt import ListCRDT


class LinkedList(object):
    def __init__(self):
        self.head = None

    def insert(self, node, left_node):
        if left_node is None:
            if self.head is None:
                self.head = node
            else:
                node.succ = self.head
                self.head.prev = node
                self.head = node
        else:
            tmp = left_node.succ
            if tmp is not None:
                tmp.prev = node
            left_node.succ = node
            node.prev = left_node
            node.succ = tmp

    def remove(self, node):
        if self.head == node:
            succ = node.succ
            if succ is not None:
                succ.prev = None
            self.head = succ
        else:
            left = node.prev
            left.succ = node.succ
            right = node.succ
            if right is not None:
                right.prev = left

        succ = node.succ
        node.succ = None
        node.prev = None

        return succ

    def __repr__(self):
        curr = self.head
        out = []
        while curr is not None:
            out.append(str(curr.id))
            curr = curr.succ
        return ','.join(out)


class Node(object):
    def __init__(self, line, vertex_id):
        self.line = line
        self.id = vertex_id
        self.succ = None
        self.prev = None

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return self.__str__()


def build_initial_state(lines, ol):
    list_crdt = ListCRDT('A', ol('A'))
    linked_list = LinkedList()
    prev = None
    ops = []
    for l in lines:
        op, _ = list_crdt.perform_op(CRDTOpAddRightLocal(l))
        assert isinstance(op, RemoteCRDTOp)

        new_node = Node(l, op.vertex_id)
        ops.append(op)
        linked_list.insert(new_node, prev)

        prev = new_node

    return list_crdt, linked_list, ops


def parse_diff(initial_content, diff, ol):
    """
    convert diff into a list of operations
    :param initial_content: The operations used to construct the initial edit
    :param ol: the ListCRDT object representiing the first edit
    :param diff: list of patches
    """

    list_crdt, linked_list, initial_ops = build_initial_state(initial_content, ol)

    # should be of the form: '@@ -x,m +y,n @@'
    print('initial state: {}'.format(list_crdt.detail_print()))
    regex = r"@@ -(.*) +(.*) @@"

    op_list = []

    for patch in diff:
        line_nums = re.search(regex, patch[0])
        x = int(line_nums.group(1).split(',')[0])
        y = int(line_nums.group(2).split(',')[0])
        curr_node = linked_list.head
        ll_index = 1

        while ll_index < y:
            curr_node = curr_node.succ
            ll_index += 1

        for i in range(1, len(patch)):
            line = patch[i]
            if line[0] == '+':
                # print('INSERTING {}'.format(line[1:]))
                # insertion
                if curr_node is None or curr_node.prev is None:
                    list_crdt.move_cursor_to(None)
                else:
                    list_crdt.move_cursor_to(curr_node.prev.id)

                op, _ = list_crdt.perform_op(CRDTOpAddRightLocal(line[1:]))
                op_list.append(op)
                new_node = Node(line[1:], op.vertex_to_add[1])
                linked_list.insert(new_node, curr_node.prev if curr_node is not None else None)
                curr_node = new_node.succ
                ll_index += 1

            elif line[0] == '-':
                # print('DELETING {}'.format(line[1:]))
                # deletion
                list_crdt.move_cursor_to(curr_node.id)
                op, _ = list_crdt.perform_op(CRDTOpDeleteLocal())
                op_list.append(op)
                curr_node = linked_list.remove(curr_node)

            else:
                # common line to both
                curr_node = curr_node.succ
                ll_index += 1

    return initial_ops + op_list, list_crdt
