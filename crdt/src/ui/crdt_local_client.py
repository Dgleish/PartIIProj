import threading
import tkinter as Tk

from crdt.crdt_ops import CRDTOpAddRightLocal, CRDTOpDeleteLocal


class CRDTLocalClient(object):
    def __init__(self, title, op_queue, move_cursor, toggle_connect, start_ops):
        self.op_q = op_queue
        self.move_cursor = move_cursor
        self.toggle_connect = toggle_connect
        self.start_ops = start_ops
        self.connected = False
        self.create_ui(title)
        # Auto connect on startup
        # self.onclick_btn(None)

    def destroy(self):
        if hasattr(self, 'root'):
            self.root.destroy()

    def create_ui(self, title):
        self.root = Tk.Tk()
        self.root.wm_title(title)
        text_frame = Tk.Frame(self.root)
        text_frame.pack(side=Tk.LEFT)
        self.t = Tk.Text(text_frame)
        self.t.pack()
        self.t.focus_set()
        self.t.bind("<Key>", self.keydown)
        self.t.bind("<ButtonRelease-1>", self.onclick_text)
        self.t.bind()
        self.cursor_pos = 0

        side_frame = Tk.Frame(self.root)
        side_frame.pack(padx=10, side=Tk.LEFT)
        self.connect_btn = Tk.Button(side_frame, text="connect")
        self.connect_btn.bind("<ButtonRelease-1>", self.onclick_btn)
        self.connect_btn.pack()
        # self.ops_btn = Tk.Button(side_frame, text="start ops")
        # self.ops_btn.bind("<ButtonRelease-1>", self.start_ops_btn)
        # self.ops_btn.pack()

    def start_ops_btn(self, event):
        self.start_ops()
        return 'break'

    def ui_toggle_connect(self):
        self.connect_btn['state'] = Tk.DISABLED
        if self.connected:
            self.connect_btn['text'] = 'disconnecting'
        else:
            self.connect_btn['text'] = 'connecting'
        self.toggle_connect()
        self.connected = not self.connected
        if self.connected:
            self.connect_btn['text'] = 'disconnect'
        else:
            self.connect_btn['text'] = 'connect'
        self.connect_btn['state'] = Tk.NORMAL

    def onclick_btn(self, event):
        t = threading.Thread(target=self.ui_toggle_connect)
        t.daemon = True
        t.start()
        return "break"

    def onclick_text(self, event):
        self.t.mark_set('insert', '1.{}'.format(self.cursor_pos))
        return "break"

    def display(self):
        self.root.mainloop()

    def update_cursor_pos(self, direction):
        if direction == 'Left':
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
        elif direction == 'Right':
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
        elif len(event.char) > 0 and 32 <= ord(event.char) <= 126:
            self.op_q.appendleft(CRDTOpAddRightLocal(event.char))
        # self.move_cursor('Right')
        return "break"

    def update(self, crdt_state):
        text, cursor = crdt_state
        self.t.delete(1.0, Tk.END)
        self.t.insert(1.0, text)
        self.cursor_pos = cursor
        self.t.mark_set("insert", '1.{}'.format(cursor))
