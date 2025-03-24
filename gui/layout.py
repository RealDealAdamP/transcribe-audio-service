# File: transcribe_audio_service/gui/layout.py

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import ttkbootstrap as ttk

from services.transcription import transcribe_file, list_audio_files
from services.utils import save_transcript
from services.version import __version__

class TranscribeAudioService:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Transcribe Audio Service v{__version__}")
        self.root.geometry("800x400")

        self.style = ttk.Style("darkly")
        self.icon_font = tkfont.Font(size=12, weight="bold")

        self.dir_var = tk.StringVar()
        self.model_var = ttk.StringVar(value="medium")
        self.lang_var = ttk.StringVar(value="en")

        self.error_messages = {}
        self.transcribe_thread = None
        self.stop_requested = False
        self.status_animation_running = False
        self.status_animation_index = 0

        self._build_ui()

    def _build_ui(self):
        # Directory selection
        ttk.Label(self.root, text="Select Directory:", bootstyle="info").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_dir = ttk.Entry(self.root, textvariable=self.dir_var, width=50, state="readonly")
        self.entry_dir.grid(row=0, column=1, padx=(5, 2), pady=5, sticky="ew")

        browse_frame = ttk.Frame(self.root)
        browse_frame.grid(row=0, column=2, padx=(2, 5), pady=5, sticky="w")
        ttk.Button(browse_frame, text="Browse", command=self.browse_directory, bootstyle="primary").pack(side="left")
        tk.Button(browse_frame, text="⟳", font=self.icon_font, width=3, command=self.refresh_directory).pack(side="left", padx=(5, 0))

        # Model selection
        ttk.Label(self.root, text="Select Whisper Model:", bootstyle="info").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        model_frame = ttk.Frame(self.root)
        model_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        for model in ["base", "small", "medium", "large"]:
            ttk.Radiobutton(model_frame, text=model, variable=self.model_var, value=model, bootstyle="success").pack(side="left", padx=5)

        # Language selection
        ttk.Label(self.root, text="Select Language:", bootstyle="info").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        lang_frame = ttk.Frame(self.root)
        lang_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        for lang, code in {"English": "en", "Spanish": "es", "French": "fr"}.items():
            ttk.Radiobutton(lang_frame, text=lang, variable=self.lang_var, value=code, bootstyle="warning").pack(side="left", padx=5)

        # File queue and output display
        queue_frame = ttk.Frame(self.root)
        queue_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        ttk.Label(queue_frame, text="Transcribe Queue:", bootstyle="info").grid(row=0, column=0, sticky="w")
        ttk.Label(queue_frame, text="Status:", bootstyle="info").grid(row=0, column=1, sticky="w")
        ttk.Label(queue_frame, text="Output:", bootstyle="info").grid(row=0, column=3, sticky="w")

        self.listbox_queue = tk.Listbox(queue_frame, width=40, height=10)
        self.listbox_queue.grid(row=1, column=0, padx=5, pady=5)
        self.status_queue = tk.Listbox(queue_frame, width=15, height=10)
        self.status_queue.grid(row=1, column=1, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(queue_frame, orient="vertical")
        scrollbar.config(command=lambda *args: (self.listbox_queue.yview(*args), self.status_queue.yview(*args)))
        scrollbar.grid(row=1, column=2, sticky="ns")

        self.listbox_queue.config(yscrollcommand=scrollbar.set)
        self.status_queue.config(yscrollcommand=scrollbar.set)

        output_frame = ttk.Frame(queue_frame)
        output_frame.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")
        self.output_box = tk.Text(output_frame, wrap="word", width=60, height=10)
        self.output_box.pack(side="left", fill="both", expand=True)
        output_scroll = ttk.Scrollbar(output_frame, command=self.output_box.yview)
        output_scroll.pack(side="right", fill="y")
        self.output_box.config(yscrollcommand=output_scroll.set)

        self.listbox_queue.bind("<<ListboxSelect>>", self.on_select_file)

        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=10, sticky="w")
        ttk.Button(button_frame, text="Transcribe", command=self.start_transcription, bootstyle="success").pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Stop", command=self.stop_transcription, bootstyle="danger").pack(side="left", padx=(0, 10))

        self.service_status = ttk.Label(button_frame, text="Service is currently Stopped", bootstyle="info")
        self.service_status.pack(side="left", padx=(10, 0))

    def browse_directory(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showerror("Error", "Cannot select new directory while transcription is running.")
            return
        directory = filedialog.askdirectory()
        if directory:
            self.dir_var.set(directory)
            self.populate_queue(directory)

    def refresh_directory(self):
        directory = self.dir_var.get()
        if not directory:
            messagebox.showerror("Error", "Please select a directory first.")
            return
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showerror("Error", "Cannot refresh while transcription is running.")
            return
        self.populate_queue(directory)

    def populate_queue(self, directory):
        self.audio_files = list_audio_files(directory)
        self.listbox_queue.delete(0, tk.END)
        self.status_queue.delete(0, tk.END)
        for file in self.audio_files:
            transcript_path = os.path.join(directory, f"{os.path.splitext(file)[0]}.txt")
            status = "Completed" if os.path.exists(transcript_path) else "In Queue"
            self.listbox_queue.insert(tk.END, file)
            self.status_queue.insert(tk.END, status)

    def start_transcription(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showinfo("Info", "Transcription already in progress.")
            return

        if not self.dir_var.get():
            messagebox.showerror("Error", "Please select a directory first.")
            return

        if self.listbox_queue.size() == 0:
            messagebox.showerror("Error", "There are no audio files in the queue.")
            return

        # Check statuses
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

        # Reset 'Error' files to 'In Queue' for retry
        for i in range(self.status_queue.size()):
            if self.status_queue.get(i) == "Error":
                self.status_queue.delete(i)
                self.status_queue.insert(i, "In Queue")

        # Begin processing
        self.stop_requested = False
        self.status_animation_running = True
        self.status_animation_index = 0
        self.animate_service_status()
        self.transcribe_thread = threading.Thread(target=self.transcribe_files, daemon=True)
        self.transcribe_thread.start()

    def transcribe_files(self):
        directory = self.dir_var.get()
        model_name = self.model_var.get()
        language = self.lang_var.get()

        any_transcribed = False

        for i in range(self.listbox_queue.size()):
            if self.stop_requested:
                self.status_animation_running = False
                self.service_status.config(text="Service is currently Stopped")
                messagebox.showinfo("Stopped", "The Active Transcriber Service has been stopped.")
                return

            filename = self.listbox_queue.get(i)
            status = self.status_queue.get(i)

            if status != "In Queue":
                continue

            file_path = os.path.join(directory, filename)
            output_path = os.path.join(directory, f"{os.path.splitext(filename)[0]}.txt")

            self.status_queue.delete(i)
            self.status_queue.insert(i, "Processing...")
            self.root.update_idletasks()

            result = transcribe_file(file_path, model_name, language)

            if "text" in result:
                try:
                    save_transcript(output_path, result["text"])
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

        if any_transcribed:
            messagebox.showinfo("Success", "All audio files have been transcribed.")

    def stop_transcription(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            self.stop_requested = True
        else:
            messagebox.showinfo("Info", "Transcription service is not running.")

    def on_select_file(self, event):
        selection = event.widget.curselection()
        if not selection:
            return

        index = selection[0]
        filename = self.listbox_queue.get(index)
        status = self.status_queue.get(index)
        directory = self.dir_var.get()
        transcript_path = os.path.join(directory, f"{os.path.splitext(filename)[0]}.txt")

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
