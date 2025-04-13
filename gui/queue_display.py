# File: gui/queue_display.py

import tkinter as tk
import ttkbootstrap as ttk
import pandas as pd
from pathlib import Path



class QueueFrame(ttk.LabelFrame):
    def __init__(self, parent, on_select_file_callback, on_double_click_file_callback, on_refresh_click=None,on_reset_queue=None, styles=None, **kwargs):
        super().__init__(parent, text="", bootstyle=styles["queue"]["frame"], padding=10, **kwargs)
        self.styles = styles
        # Animation state for cluster plot
        self.cluster_animation_running = False
        self.cluster_animation_label = None


        self.grid_rowconfigure(1, weight=1, minsize=310) 
        # ────────────────
        # Top-Left Refresh Button (now in col 0)
        if on_refresh_click:
            ttk.Button(self, 
                       text="↻",
                       style="IconWarning.TButton",
                       width=3, 
                       command=on_refresh_click).grid(row=0, column=0, sticky="nw", padx=4, pady=5)
        
        # Top-Left Reset Queue Button (now in col 0)
        if on_reset_queue:
            ttk.Button(self, 
                       text="❌",
                       style="IconWarning.TButton", 
                       width=3, 
                       command=on_reset_queue).grid(row=1, column=0, sticky="nw", padx=4, pady=5)    
        


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
        search_entry.bind("<KeyRelease>", self.handle_search_input)

       
        # Step 0: Cluster label ABOVE the wrapper — no shift in wrapper height
        self.cluster_label = ttk.Label(
            self,
            text="Speaker Identification Clusters:",
            bootstyle=styles["queue"]["label_cluster"],
            anchor="center",
            justify="center"
        )
        self.cluster_label.grid(row=0, column=5, sticky="ew", padx=(0, 5), pady=(10, 0))


        # Step 1: Cluster plot wrapper aligned with output text height
        self.cluster_plot_wrapper = ttk.Frame(self, width=400, height=300)
        self.cluster_plot_wrapper.grid(row=1, column=5, padx=(0, 5), pady=5, sticky="nsew")

        # 🔒 Prevent auto-resize of the wrapper
        self.cluster_plot_wrapper.grid_propagate(False)
        self.cluster_plot_wrapper.pack_propagate(False)

        # Step 2: Plot display area inside wrapper
        self.cluster_plot_frame = tk.LabelFrame(
            self.cluster_plot_wrapper,
            text="",
            bg="#191919",   # Match dark mode
            bd=1,
            relief="solid"
        )
        self.cluster_plot_frame.pack(fill="both", expand=True)

        # Step 3: Placeholder for canvas
        self.cluster_plot_canvas = None
                                    

        # ────────────────
        # Wrapper frame to hold both listboxes + scrollbar
        queue_frame_wrapper = ttk.Frame(self)
        queue_frame_wrapper.grid(row=1, column=1, columnspan=3, sticky="nsew", padx=5, pady=5)
        

        # Transcribe Queue listbox
        self.listbox_queue = tk.Listbox(queue_frame_wrapper, width=40, height=20)
        self.listbox_queue.grid(row=0, column=0, sticky="nsew")
        self.listbox_queue.bind("<Double-1>", on_double_click_file_callback)
        self.listbox_queue.bind("<<ListboxSelect>>", on_select_file_callback)
        self.listbox_queue.bind("<MouseWheel>", self.sync_scroll)

        # Status Queue listbox
        self.status_queue = tk.Listbox(queue_frame_wrapper, width=15, height=20)
        self.status_queue.grid(row=0, column=1, sticky="nsew")
        self.status_queue.bind("<MouseWheel>", self.sync_scroll)

        # Shared vertical scrollbar
        scrollbar = ttk.Scrollbar(queue_frame_wrapper, orient="vertical")
        scrollbar.grid(row=0, column=2, sticky="ns")
        scrollbar.config(command=lambda *args: (
            self.listbox_queue.yview(*args),
            self.status_queue.yview(*args))
        )

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
    
    def sync_scroll(self, event):
        # Determine scroll direction
        delta = int(-1 * (event.delta / 120))  # Windows
        self.listbox_queue.yview_scroll(delta, "units")
        self.status_queue.yview_scroll(delta, "units")
        return "break"  # Prevent default behavior

    def handle_search_input(self, event=None):
        keyword = self.search_var.get().strip()

        # Init config if not already
        if not hasattr(self, "last_search_term"):
            self.last_search_term = ""
            self.search_matches = []
            self.current_match_index = -1

        is_enter = event and event.keysym == "Return"
        keyword_changed = keyword != self.last_search_term

        if keyword_changed:
            self.last_search_term = keyword
            self.search_matches = []
            self.current_match_index = -1
            self.output_box.tag_remove("highlight", "1.0", tk.END)
            self.output_box.tag_remove("active_match", "1.0", tk.END)

            if len(keyword) < 2:
                return

            self.output_box.tag_configure("highlight", background="orange", foreground="black")
            self.output_box.tag_configure("active_match", background="#77b303", foreground="black")

            start = "1.0"
            while True:
                pos = self.output_box.search(keyword, start, stopindex=tk.END, nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                self.output_box.tag_add("highlight", pos, end)
                self.search_matches.append((pos, end))
                start = end

            if self.search_matches:
                self.current_match_index = 0
                start, end = self.search_matches[0]
                self.output_box.tag_add("active_match", start, end)
                self.scroll_to_match(start, set_focus=False)

        elif is_enter and self.search_matches:
            # Remove previous active highlight
            self.output_box.tag_remove("active_match", "1.0", tk.END)

            # Check if Shift is held (state bitmask 0x0001 on Windows/Linux)
            reverse = (event.state & 0x0001) != 0

            if reverse:
                self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
            else:
                self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)

            start, end = self.search_matches[self.current_match_index]
            self.output_box.tag_add("active_match", start, end)
            self.scroll_to_match(start, set_focus=False)

            # Restore focus to entry field
            if event:
                event.widget.focus_set()

        return "break"





    def highlight_keywords(self):
        keyword = self.search_var.get().strip()
        self.output_box.tag_remove("highlight", "1.0", tk.END)
        self.output_box.tag_remove("active_match", "1.0", tk.END)

        self.search_matches = []
        self.current_match_index = -1

        if len(keyword) < 2:
            return

        self.output_box.tag_configure("highlight", background="orange", foreground="black")
        self.output_box.tag_configure("active_match", background="yellow", foreground="black")

        start = "1.0"
        while True:
            pos = self.output_box.search(keyword, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(keyword)}c"
            self.output_box.tag_add("highlight", pos, end)
            self.search_matches.append((pos, end))  # Save both start and end
            start = end

        if self.search_matches:
            self.current_match_index = 0
            self.output_box.tag_add("active_match", *self.search_matches[0])
            self.scroll_to_match(self.search_matches[0][0], set_focus=False)


    def scroll_to_match(self, index, set_focus=True):
        self.output_box.see(index)  # Vertical scroll

        # Move to position and adjust horizontal scroll
        self.output_box.mark_set("insert", index)
        self.output_box.xview_moveto(self.output_box.index("insert").split(".")[1])

        # Only set focus if explicitly requested
        if set_focus:
            self.output_box.focus()
            
    def jump_to_next_match(self, event=None):
        if not self.search_matches:
            return "break"

        # Remove previous active match tag
        self.output_box.tag_remove("active_match", "1.0", tk.END)

        # Advance to next match
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        start, end = self.search_matches[self.current_match_index]

        # Apply active match tag
        self.output_box.tag_add("active_match", start, end)

        # Scroll to new match start (just vertical/horizontal centering)
        self.scroll_to_match(start, set_focus=False)

        # Return focus to search entry field
        if event:
            event.widget.focus_set()

        return "break"

              
    def configure_output_display(self, wrap_mode="word", use_horizontal_scroll=False):
        self.output_box.config(wrap=wrap_mode)

        if use_horizontal_scroll:
            self.output_scroll_h.pack(side="bottom", fill="x")
        else:
            self.output_scroll_h.pack_forget()


    def display_cluster_plot(self, filename):
        cluster_dir = Path("cluster_data")
        stem = Path(filename).stem
        cluster_path = cluster_dir / f"{stem}_umap.feather"

        for widget in self.cluster_plot_frame.winfo_children():
            widget.destroy()

        if not cluster_path.exists():
            self.set_cluster_status("❌ Cluster Data Missing")
            return

        self._render_cluster_plot(cluster_path)
        self.cluster_animation_running = False

    def _render_cluster_plot(self, cluster_path):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import pandas as pd

        df = pd.read_feather(cluster_path)
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor("#191919")
        ax.set_facecolor("#191919")
        ax.tick_params(colors='white')
        ax.set_title("", color="white", fontname="Courier New")

        unique_labels = sorted(df["speaker_id"].unique())
        cmap = plt.get_cmap("tab10")

        for idx, label in enumerate(unique_labels):
            mask = df["speaker_id"] == label
            color = cmap(idx % 10)
            ax.scatter(df.loc[mask, "x"], df.loc[mask, "y"], color=color, s=18, alpha=0.8, linewidths=0)

        legend_handles = [
            plt.Line2D([], [], marker='o', color='none', markerfacecolor=cmap(idx % 10),
                    markeredgecolor='none', markersize=8, linestyle='None',
                    label=f"Speaker {label}" if label != -1 else "Unidentified")
            for idx, label in enumerate(unique_labels)
        ]
        ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.15),
                ncol=2, fontsize=10, frameon=False, labelcolor="white")

        ax.set_xticklabels([]), ax.set_yticklabels([]), ax.grid(False)
        for spine in ax.spines.values():
            spine.set_edgecolor("white")

        fig.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=self.cluster_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.cluster_plot_canvas = canvas
        plt.close(fig)



    def set_cluster_status(self, text, animate=False):
        # Clear existing widgets
        for widget in self.cluster_plot_frame.winfo_children():
            widget.destroy()

        self.cluster_animation_running = animate
        self.cluster_animation_dots = 0
        self.cluster_animation_base_text = text.lstrip("⏳✅❌⚠️").strip()

        # New Frame to hold ⏳ and text separately
        wrapper = ttk.Frame(self.cluster_plot_frame, style="TFrame")
        wrapper.pack(expand=True, fill="both", pady=(10, 0))

        # Static "⏳" symbol
        self.cluster_icon_label = ttk.Label(
            wrapper,
            text="⏳",
            font=("Courier New", 12),
            background="#060606",
            foreground="white",
            anchor="center"
        )
        self.cluster_icon_label.pack(side="left", padx=(10, 5))

        # Dynamic status text label
        self.cluster_animation_label = ttk.Label(
            wrapper,
            text=self.cluster_animation_base_text,
            font=("Courier New", 10),
            background="#060606",
            foreground="white",
            anchor="w",
            justify="left"
        )
        self.cluster_animation_label.pack(side="left", fill="x", expand=True)

        if animate:
            self._run_cluster_animation()


    def _run_cluster_animation(self):
        if not self.cluster_animation_running or not self.cluster_animation_label:
            return

        try:
            dots = "." * (self.cluster_animation_dots % 4)
            self.cluster_animation_label.config(text=f"{self.cluster_animation_base_text}{dots}")
            self.cluster_animation_dots += 1
            self.after(500, self._run_cluster_animation)
        except (tk.TclError, AttributeError):
            self.cluster_animation_running = False
            self.cluster_animation_label = None   

    def show_cluster_placeholder(self, message="❌ No Cluster Data Available"):
        for widget in self.cluster_plot_frame.winfo_children():
            widget.destroy()

        label = ttk.Label(
            self.cluster_plot_frame,
            text=message,
            font=("Courier New", 10),
            background="#191919",
            foreground="white",
            anchor="center",
            justify="center"
        )
        label.pack(expand=True, fill="both")

    