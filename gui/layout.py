# File: gui/layout.py

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import ttkbootstrap as ttk

from gui.settings_panel import create_settings_panel
from gui.queue_display import create_queue_display
from gui.button_controls import create_button_controls

from gui.style_config import get_theme_style, get_bootstyles

from services.transcription import transcribe_file, list_audio_files
from services.utils import save_transcript
from services.version import __version__

from services.template_manager import TemplateManager


class TranscribeAudioService:
    def __init__(self, root):
        self.root = root
        self._configure_root_window()

        # Load global style and font
        self.style, self.icon_font = get_theme_style()
        self.styles = get_bootstyles()

        # Global state variables
        self.dir_var = tk.StringVar()
        self.model_var = ttk.StringVar(value="medium")
        self.lang_var = ttk.StringVar(value="en")
       
        self.output_format_var = tk.StringVar(value="txt")
        self.output_format_var.trace_add("write", self.on_output_format_change) #assigns callback to output format variable

        self.speaker_recognition_var = tk.BooleanVar()

        # Control flags
        self.error_messages = {}
        self.transcribe_thread = None
        self.stop_requested = False
        self.status_animation_running = False
        self.status_animation_index = 0

        # Initialize template manager
        self.template_manager = TemplateManager()
        self.active_template = None

        #Set 

        # Build UI
        self._build_ui()

    def _configure_root_window(self):
        self.root.title(f"Transcribe Audio Service v{__version__}")
        self.root.geometry("800x500")

    def _build_ui(self):
        # Row 0 — Directory Selection
        ttk.Label(self.root, text="Select Directory:", bootstyle="info").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_dir = ttk.Entry(self.root, textvariable=self.dir_var, width=50, state="readonly")
        self.entry_dir.grid(row=0, column=1, padx=(5, 2), pady=5, sticky="ew")

        browse_frame = ttk.Frame(self.root)
        browse_frame.grid(row=0, column=2, padx=(2, 5), pady=5, sticky="w")
        ttk.Button(browse_frame, text="Browse", command=self.browse_directory, bootstyle="primary").pack(side="left")
        tk.Button(browse_frame, text="⟳", font=self.icon_font, width=3, command=self.refresh_directory).pack(side="left", padx=(5, 0))

        # Row 1–2 — Settings Panel
        settings_frame, self.model_buttons, self.lang_buttons, self.output_buttons, self.speaker_checkbox = create_settings_panel(
            self.root, self.model_var, self.lang_var, self.output_format_var, self.speaker_recognition_var
        )
        settings_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=(15, 20), sticky="w")

        # Row 3 — Queue and Output Display
        queue_frame, self.listbox_queue, self.status_queue, self.output_box = create_queue_display(self.root,self.on_select_file,self.on_double_click_file)
        queue_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # Row 4 — Bottom Controls
        button_frame, self.service_status = create_button_controls(
            self.root, self.start_transcription, self.stop_transcription
        )
        button_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=10, sticky="w")

    # ────────────────────────────────────────────────
    # Helper Methods
    # ────────────────────────────────────────────────

    def set_ui_inputs_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in self.model_buttons + self.lang_buttons + self.output_buttons:
            btn.config(state=state)
        self.speaker_checkbox.config(state=state)

    def browse_directory(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showerror("Error", "Cannot select new directory while transcription is running.")
            return
        directory = filedialog.askdirectory()
        if directory:
            self.dir_var.set(directory)
            self.populate_queue(self.dir)

    def refresh_directory(self):
        if not self.dir:
            messagebox.showerror("Error", "Please select a directory first.")
            return
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showerror("Error", "Cannot refresh while transcription is running.")
            return
        # Clear output box text
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.config(state="disabled")
        #re populate queue
        self.populate_queue(self.dir)

    def populate_queue(self, directory):
        self.audio_files = list_audio_files(directory)
        self.listbox_queue.delete(0, tk.END)
        self.status_queue.delete(0, tk.END)
        for file in self.audio_files:
            transcript_path = os.path.join(directory, f"{os.path.splitext(file)[0]}.{self.output_extension}")
            status = "Completed" if os.path.exists(transcript_path) else "In Queue"
            self.listbox_queue.insert(tk.END, file)
            self.status_queue.insert(tk.END, status)

    def start_transcription(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showinfo("Info", "Transcription already in progress.")
            return

        if not self.dir:
            messagebox.showerror("Error", "Please select a directory first.")
            return

        if self.listbox_queue.size() == 0:
            messagebox.showerror("Error", "There are no audio files in the queue.")
            return

        all_completed = True
        any_retriable = False

        for i in range(self.status_queue.size()):
            status = self.status_queue.get(i)
            if status in ("In Queue", "Error"):
                all_completed = False
                any_retriable = True
                break

        if all_completed:
            messagebox.showinfo("Info", "All audio files have transcribed successfully.")
            return

        if not any_retriable:
            messagebox.showerror("Error", "No transcribable files available.")
            return

        for i in range(self.status_queue.size()):
            if self.status_queue.get(i) == "Error":
                self.status_queue.delete(i)
                self.status_queue.insert(i, "In Queue")

        self.active_template = self.template_manager.get_template(self.output_extension)

        self.stop_requested = False
        self.status_animation_running = True
        self.status_animation_index = 0
        self.set_ui_inputs_state(False)
        self.animate_service_status()
        self.transcribe_thread = threading.Thread(target=self.transcribe_files, daemon=True)
        self.transcribe_thread.start()

    def transcribe_files(self):
        any_transcribed = False

        for i in range(self.listbox_queue.size()):
            if self.stop_requested:
                self.status_animation_running = False
                self.service_status.config(text="Service is currently Stopped")
                self.set_ui_inputs_state(True)
                messagebox.showinfo("Stopped", "The Active Transcriber Service has been stopped.")
                return

            filename = self.listbox_queue.get(i)
            status = self.status_queue.get(i)
            if status != "In Queue":
                continue

            file_path = os.path.join(self.dir, filename)
            output_path = os.path.join(self.dir, f"{os.path.splitext(filename)[0]}.{self.output_extension}")

            self.status_queue.delete(i)
            self.status_queue.insert(i, "Processing...")
            self.root.update_idletasks()

            result = transcribe_file(file_path, self.model, self.language, return_segments=self.use_diarization)

            if "text" in result:
                try:
                    save_transcript(output_path,
                                    result["text"],
                                    self.active_template,
                                    input_file=file_path,
                                    output_format=self.output_extension)

                    self.status_queue.delete(i)
                    self.status_queue.insert(i, "Completed")
                    any_transcribed = True
                except Exception as e:
                    self.status_queue.delete(i)
                    self.status_queue.insert(i, "Error")
                    self.error_messages[filename] = f"Failed to save transcript: {str(e)}"
            else:
                self.status_queue.delete(i)
                self.status_queue.insert(i, "Error")
                self.error_messages[filename] = result.get("error", "Unknown error")

        self.status_animation_running = False
        self.service_status.config(text="Service is currently Stopped")
        self.set_ui_inputs_state(True)

        if any_transcribed:
            messagebox.showinfo("Success", "All audio files have been transcribed.")

    def stop_transcription(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            self.stop_requested = True
        else:
            messagebox.showinfo("Info", "Transcription service is not running.")
    
    def on_double_click_file(self, event):
        selection = event.widget.curselection() # event.widget is a tk.Listbox at runtime, not recognized in VS code
        if not selection:
            return

        index = selection[0]
        filename = self.listbox_queue.get(index)
        status = self.status_queue.get(index)
        transcript_path = os.path.join(self.dir, f"{os.path.splitext(filename)[0]}.{self.output_extension}")

        if status == "Completed" and os.path.exists(transcript_path):
            try:
                os.startfile(transcript_path)  # Windows-specific
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{e}")
        else:
            messagebox.showinfo("No File Found", "This file has not been transcribed yet.")

    def on_select_file(self, event):
        selection = event.widget.curselection() # event.widget is a tk.Listbox at runtime, not recognized in VS code
        if not selection:
            return

        index = selection[0]
        filename = self.listbox_queue.get(index)
        status = self.status_queue.get(index)
        transcript_path = os.path.join(self.dir, f"{os.path.splitext(filename)[0]}.{self.output_extension}")

        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)

        if status == "Completed" and os.path.exists(transcript_path):
            with open(transcript_path, "r", encoding="utf-8") as f:
                self.output_box.insert(tk.END, f.read())
        elif status == "Error":
            error_msg = self.error_messages.get(filename, "An unknown error occurred.")
            self.output_box.insert(tk.END, f"Transcription Error:\n{error_msg}")
        else:
            self.output_box.insert(tk.END, "No Transcription Detected")

        self.output_box.config(state="disabled")

    def animate_service_status(self):
        if not self.status_animation_running:
            return
        dots = "." * (self.status_animation_index % 4)
        self.service_status.config(text=f"Service is currently running{dots}")
        self.status_animation_index += 1
        self.root.after(500, self.animate_service_status)

    def on_output_format_change(self, *args):
        if not self.dir:
            return
        self.refresh_directory()
        messagebox.showinfo(
            "Output Format Changed",
            "The output format has been updated.\nThe queue has been refreshed."
            )

    # ────────────────────────────────────────────────
    # UI Property Accessors
    # ────────────────────────────────────────────────

    @property
    def dir(self):
        return self.dir_var.get()

    @property
    def model(self):
        return self.model_var.get()

    @property
    def language(self):
        return self.lang_var.get()

    @property
    def output_extension(self):
        return self.output_format_var.get()

    @property
    def use_diarization(self):
        return self.speaker_recognition_var.get()
