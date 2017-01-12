import Tkinter as Tk

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal


class CRDTLocalClient(object):
    def __init__(self, op_queue):
        self.op_q = op_queue
        self.create_ui()

    def create_ui(self):
        self.root = Tk.Tk()
        text_frame = Tk.Frame(self.root)
        text_frame.pack(side=Tk.LEFT)
        self.t = Tk.Text(text_frame)
        self.t.pack()
        self.t.focus_set()
        self.t.bind("<Key>", self.keydown)

        side_frame = Tk.Frame(self.root)
        side_frame.pack(padx=10, side=Tk.LEFT)
        btn = Tk.Button(side_frame, text="button")
        btn.pack()

    def display(self):
        self.root.mainloop()

    def keydown(self, event):
        if event.char == '\x08':
            self.op_q.appendleft(CRDTOpDeleteLocal())
        else:
            self.op_q.appendleft(CRDTOpAddRightLocal(event.char))
        return "break"

    def update(self, text, cursor):
        self.t.delete(1.0, Tk.END)
        self.t.insert(1.0, text)
        self.t.mark_set("insert", "%d.%d" % (1, cursor))


if __name__ == '__main__':
    CRDTLocalClient([])
