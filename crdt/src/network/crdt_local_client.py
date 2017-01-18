import Tkinter as Tk

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal


class CRDTLocalClient(object):
    def __init__(self, op_queue, move_cursor):
        self.op_q = op_queue
        self.move_cursor = move_cursor
        self.create_ui()

    def create_ui(self):
        self.root = Tk.Tk()
        text_frame = Tk.Frame(self.root)
        text_frame.pack(side=Tk.LEFT)
        self.t = Tk.Text(text_frame)
        self.t.pack()
        self.t.focus_set()
        self.t.bind("<Key>", self.keydown)
        self.t.bind("<ButtonRelease-1>", self.onclick)
        self.t.bind()
        self.cursor_pos = 0

        side_frame = Tk.Frame(self.root)
        side_frame.pack(padx=10, side=Tk.LEFT)
        btn = Tk.Button(side_frame, text="button")
        btn.pack()

    def onclick(self, event):
        return "break"

    def display(self):
        self.root.mainloop()

    def update_cursor_pos(self, dir):
        if dir == 'Left':
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
        elif dir == 'Right':
            self.cursor_pos += 1

    def keydown(self, event):
        # ind = self.t.index(Tk.INSERT)
        # print ind
        if event.keysym == 'Right' or event.keysym == 'Left':
            self.move_cursor(event.keysym)
            self.update_cursor_pos(event.keysym)
            return
        elif event.char == '\x08':
            self.op_q.appendleft(CRDTOpDeleteLocal())
        elif len(event.char) > 0 and ord(event.char) >= 32 and ord(event.char) <= 126:
            self.op_q.appendleft(CRDTOpAddRightLocal(event.char))
        # self.move_cursor('Right')
        return "break"

    def update(self, (text, cursor)):
        print cursor
        self.t.delete(1.0, Tk.END)
        self.t.insert(1.0, text)
        self.t.mark_set("insert", '1.{}'.format(cursor))

