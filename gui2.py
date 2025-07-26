import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Custom Tkinter Layout")
        self.minsize(300, 300)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.create_center()
        self.create_footer()

        self.bind("<Configure>", self.on_resize)

    def create_header(self):
        self.header_frame = tk.Frame(self, bg="#dddddd")
        self.header_frame.grid(row=0, column=0, sticky="nsew")
        self.header_frame.grid_propagate(False)

        self.header_buttons = [tk.Button(self.header_frame, text=f"Btn{i+1}") for i in range(3)]
        for btn in self.header_buttons:
            btn.pack(side="left", padx=2, pady=5)

    def create_center(self):
        self.center_frame = tk.Frame(self, bg="white")
        self.center_frame.grid(row=1, column=0, sticky="nsew")

        # Scrollable canvas
        self.canvas = tk.Canvas(self.center_frame, borderwidth=0, background="white")
        self.scroll_frame = tk.Frame(self.canvas, background="white")
        self.v_scroll = tk.Scrollbar(self.center_frame, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=self.v_scroll.set)
        self.v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", tags="inner")

        self.scroll_frame.bind("<Configure>", self.on_frame_configure)

        for i in range(10):
            self.add_row(i)

    def add_row(self, index):
        row = tk.Frame(self.scroll_frame, pady=5)
        row.pack(fill="x", expand=True)

        label = tk.Label(row, text=f"Item {index}\nDescription", justify="right", anchor="e")
        label.pack(side="left", fill="x", expand=True)

        spin = tk.Spinbox(row, from_=0, to=100, width=5)
        spin.pack(side="left", padx=4, ipadx=10)

        btn1 = tk.Button(row, text="Edit", width=5)
        btn1.pack(side="left", padx=2)
        btn2 = tk.Button(row, text="Del", width=5)
        btn2.pack(side="left", padx=2)

    def create_footer(self):
        self.footer_frame = tk.Frame(self, bg="#f0f0f0")
        self.footer_frame.grid(row=2, column=0, sticky="nsew")
        self.footer_frame.grid_propagate(False)

        self.footer_frame.grid_rowconfigure(0, weight=1)
        self.footer_frame.grid_rowconfigure(1, weight=1)
        self.footer_frame.grid_columnconfigure(0, weight=1)

        top_row = tk.Frame(self.footer_frame)
        top_row.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        top_row.grid_columnconfigure(0, weight=9)
        top_row.grid_columnconfigure(1, weight=1)

        self.selector = ttk.Combobox(top_row, values=["Option 1", "Option 2"])
        self.selector.grid(row=0, column=0, sticky="ew", padx=(10, 5))
        self.find_button = tk.Button(top_row, text="Find")
        self.find_button.grid(row=0, column=1, sticky="ew", padx=(5, 10))

        bottom_row = tk.Frame(self.footer_frame)
        bottom_row.grid(row=1, column=0, sticky="e", padx=10, pady=(0, 10))

        for i in range(3):
            tk.Button(bottom_row, text=f"Action {i+1}").pack(side="right", padx=5)

    def on_resize(self, event):
        win_h = self.winfo_height()

        header_h = min(max(40, int(0.1 * win_h)), 100)
        center_h = min(max(200, int(0.7 * win_h)), int(0.7 * win_h))
        footer_h = min(max(80, int(0.2 * win_h)), int(0.2 * win_h))

        self.header_frame.config(height=header_h)
        # self.center_frame.config(height=center_h)
        self.footer_frame.config(height=footer_h)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
