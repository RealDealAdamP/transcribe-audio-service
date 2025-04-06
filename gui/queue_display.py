# File: gui/queue_display.py

import tkinter as tk
import ttkbootstrap as ttk

class QueueFrame(ttk.LabelFrame):
    def __init__(self, parent, on_select_file_callback, on_double_click_file_callback, on_refresh_click=None, styles=None, **kwargs):
        super().__init__(parent, text="", bootstyle=styles["queue"]["frame"], padding=10, **kwargs)
        self.styles = styles

        # ────────────────
        # Top-Left Refresh Button (now in col 0)
        if on_refresh_click:
            ttk.Button(self, text="⟳",bootstyle=styles["queue"]["button_refresh"], width=3, command=on_refresh_click).grid(row=0, column=0, sticky="nw", padx=5, pady=5)

        # ────────────────
        # Queue + Status Labels 
        ttk.Label(self, text="Transcribe Queue:", bootstyle=styles["queue"]["label_queue"]).grid(row=0, column=1, sticky="w")
        ttk.Label(self, text="Status:", bootstyle=styles["queue"]["label_status"]).grid(row=0, column=2, sticky="w")
        
        
        # Output Text Label + Search Entry Frame 
        output_label_frame = ttk.Frame(self)
        output_label_frame.grid(row=0, column=4, columnspan=2, sticky="w", padx=(0, 5))
        
        # Output Text Label
        ttk.Label(output_label_frame, text="Output Text:", bootstyle=styles["queue"]["label_output_txt"]).pack(side="left")

        # Search Entry
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(output_label_frame, textvariable=self.search_var,bootstyle=styles["queue"]["entry_search"], width=57)
        search_entry.pack(side="left", padx=(5, 0))
        search_entry.bind("<KeyRelease>", lambda event: self.highlight_keywords())
       

        # ────────────────
        # Listboxes
        self.listbox_queue = tk.Listbox(self, width=40, height=15)
        self.listbox_queue.grid(row=1, column=1, padx=5, pady=5)
        self.listbox_queue.bind("<Double-1>", on_double_click_file_callback)
        self.listbox_queue.bind("<<ListboxSelect>>", on_select_file_callback)

        self.status_queue = tk.Listbox(self, width=15, height=15)
        self.status_queue.grid(row=1, column=2, padx=5, pady=5)

        # Shared scrollbar (col 3)
        scrollbar = ttk.Scrollbar(self, orient="vertical")
        scrollbar.config(command=lambda *args: (self.listbox_queue.yview(*args), self.status_queue.yview(*args)))
        scrollbar.grid(row=1, column=3, sticky="ns")

        self.listbox_queue.config(yscrollcommand=scrollbar.set)
        self.status_queue.config(yscrollcommand=scrollbar.set)

        # Output Box (col 4)
        output_frame = ttk.Frame(self)
        output_frame.grid(row=1, column=4, padx=5, pady=5, sticky="nsew")

        # Inner frame to stack text box and horizontal scrollbar
        text_wrapper = ttk.Frame(output_frame)
        text_wrapper.pack(side="left", fill="both", expand=True)

        # Text Widget
        self.output_box = tk.Text(
                text_wrapper,
                wrap="none",  # since we want horizontal scroll support
                font=("Courier New", 10),
                width=50,
                height=10,
                state="disabled"
            )
        self.output_box.pack(side="top", fill="both", expand=True)

        # Horizontal Scrollbar (BOTTOM, matching width)
        self.output_scroll_h = ttk.Scrollbar(
            text_wrapper,
            orient="horizontal",
            command=self.output_box.xview
        )
        self.output_scroll_h.pack(side="bottom", fill="x")
        self.output_box.config(xscrollcommand=self.output_scroll_h.set)

        # Vertical Scrollbar (same as before)
        output_scroll = ttk.Scrollbar(output_frame, command=self.output_box.yview)
        output_scroll.pack(side="right", fill="y")
        self.output_box.config(yscrollcommand=output_scroll.set)

    def get_queue_widgets(self):
        return self.listbox_queue, self.status_queue, self.output_box

    def highlight_keywords(self):
        keyword = self.search_var.get().strip()
        self.output_box.tag_remove("highlight", "1.0", tk.END)  # Always remove old highlights

        if len(keyword) < 2:
            return  # Don't add new highlights for short terms

        self.output_box.tag_configure("highlight", background="orange", foreground="black")

        start = "1.0"
        while True:
            pos = self.output_box.search(keyword, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(keyword)}c"
            self.output_box.tag_add("highlight", pos, end)
            start = end
              
    def configure_output_display(self, wrap_mode="word", use_horizontal_scroll=False):
        self.output_box.config(wrap=wrap_mode)

        if use_horizontal_scroll:
            self.output_scroll_h.pack(side="bottom", fill="x")
        else:
            self.output_scroll_h.pack_forget()