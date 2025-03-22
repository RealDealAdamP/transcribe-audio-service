# Standard Library
import os
import threading
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont

# Third-party
import whisper
import ttkbootstrap as ttk


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        messagebox.showerror(
            title="Missing Dependency",
            message=(
                "FFmpeg is not installed or not added to your system PATH.\n\n"
                "Please install FFmpeg and make sure it's accessible via command line.\n"
                "Download: https://ffmpeg.org/download.html"
            )
        )
        return False
    return True

class TranscribeAudioService:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcribe Audio Service")
        self.root.geometry("800x400")  # Increased width for status column
        
        # Apply ttkbootstrap theme
        self.style = ttk.Style("darkly")

        #set tk button icon font for refresh indicator
        self.icon_font = tkfont.Font(size=12, weight="bold")

         # Directory Select Icon
        ttk.Label(root, text="Select Directory:", bootstyle="info").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        #Directory Select Txt Field
        self.dir_var = tk.StringVar()
        self.entry_dir = ttk.Entry(root, textvariable=self.dir_var, width=50, state="readonly")
        self.entry_dir.grid(row=0, column=1, padx=(5, 2), pady=5, sticky="ew")

        # Browse + Refresh Button Group
        browse_refresh_frame = ttk.Frame(root)
        browse_refresh_frame.grid(row=0, column=2, padx=(2, 5), pady=5, sticky="w")

        # Browse Button
        ttk.Button(browse_refresh_frame, text="Browse", command=self.browse_directory, bootstyle="primary").pack(side="left")
        # Refresh Button
        tk.Button(browse_refresh_frame,text="⟳",font=self.icon_font,width=3,command=self.refresh_directory).pack(side="left", padx=(5, 0))


        # Whisper Model Selection
        model_frame = ttk.Frame(root)
        model_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(root, text="Select Whisper Model:", bootstyle="info").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.model_var = ttk.StringVar(value="medium")
        self.models = ["base", "small", "medium", "large"]
        for model in self.models:
            ttk.Radiobutton(model_frame, text=model, variable=self.model_var, value=model, bootstyle="success").pack(side="left", padx=5)

        # Language Selection
        lang_frame = ttk.Frame(root)
        lang_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(root, text="Select Language:", bootstyle="info").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.lang_var = ttk.StringVar(value="en")
        self.languages = {"English": "en", "Spanish": "es", "French": "fr"}
        for lang, code in self.languages.items():
            ttk.Radiobutton(lang_frame, text=lang, variable=self.lang_var, value=code, bootstyle="warning").pack(side="left", padx=5)

        # Create Frame to hold Listboxes & Labels
        queue_frame = ttk.Frame(root)
        queue_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # Labels inside queue_frame
        ttk.Label(queue_frame, text="Transcribe Queue:", bootstyle="info").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(queue_frame, text="Status:", bootstyle="info").grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(queue_frame, text="Output:", bootstyle="info").grid(row=0, column=3, padx=5, pady=2, sticky="w")

        # Scrollbar for both Queue and Status Listboxes
        listbox_scrollbar = ttk.Scrollbar(queue_frame, orient="vertical")

         # Audio File Listbox
        self.listbox_queue = tk.Listbox(queue_frame, width=40, height=10, yscrollcommand=listbox_scrollbar.set)
        self.listbox_queue.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Status Listbox
        self.status_queue = tk.Listbox(queue_frame, width=15, height=10, yscrollcommand=listbox_scrollbar.set)
        self.status_queue.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Attach scrollbar to both Listboxes
        listbox_scrollbar.config(command=lambda *args: (self.listbox_queue.yview(*args), self.status_queue.yview(*args)))
        listbox_scrollbar.grid(row=1, column=2, sticky="ns")  # Placed beside Status Listbox in column 2

        # Output Text Widget with Scrollbar
        output_frame = ttk.Frame(queue_frame)
        output_frame.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")

        self.output_box = tk.Text(output_frame, wrap="word", width=60, height=10)
        self.output_box.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(output_frame, command=self.output_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.output_box.config(yscrollcommand=scrollbar.set)

        # Bind selection to display output
        self.listbox_queue.bind("<<ListboxSelect>>", self.on_select_file)



        # Transcribe + Stop Button Group 
        button_frame = ttk.Frame(root)
        button_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=10, sticky="w")

        ttk.Button(button_frame, text="Transcribe", command=self.start_transcription, bootstyle="active").pack(side="left", padx=(0, 10))

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_transcription, bootstyle="danger")
        self.stop_button.pack(side="left", padx=(0, 10))


        #Stop button attributes
        self.transcribe_thread = None
        self.stop_requested = False

        # Service Status Label (initially 'stopped')
        self.service_status = ttk.Label(button_frame, text="Service is currently Stopped", bootstyle="info")
        self.service_status.pack(side="left", padx=(10, 0))

        self.status_animation_running = False
        self.status_animation_index = 0

    def browse_directory(self):
        """Populates the queue with files and assigns initial statuses."""

        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showerror("Error", "Cannot select new directory when service is running.")
            return
        
        directory = filedialog.askdirectory()
        if directory:
            self.dir_var.set(directory)
            self.populate_queue(directory)

    def refresh_directory(self):
        """Refresh queue based on existing directory entry, with checks."""
        directory = self.dir_var.get()

        if not directory:
            messagebox.showerror("Error", "Please select a directory first.")
            return

        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showerror("Error", "Selected directory cannot refresh when service is running.")
            return
        
        self.populate_queue(directory)


    def stop_transcription(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            self.stop_requested = True  # Flag will be read in transcribe_files()
        else:
            messagebox.showinfo("Info", "Transcribe Audio Service is not currently active.")

    def populate_queue(self, directory):
        """Lists .mp3 and .wav files, checking if transcriptions exist."""
        self.listbox_queue.delete(0, tk.END)
        self.status_queue.delete(0, tk.END)

        for file in os.listdir(directory):
            if file.lower().endswith((".mp3", ".wav")):
                audio_path = os.path.join(directory, file)
                transcript_path = os.path.join(directory, f"{os.path.splitext(file)[0]}.txt")

                # Assign status based on whether the transcription exists
                status = "Completed" if os.path.exists(transcript_path) else "In Queue"

                self.listbox_queue.insert(tk.END, file)
                self.status_queue.insert(tk.END, status)

    def animate_service_status(self):
        if not self.status_animation_running:
            return

        dots = "." * (self.status_animation_index % 4)
        self.service_status.config(text=f"Service is currently running{dots}")
        self.status_animation_index += 1

        # Call again after 500ms
        self.root.after(500, self.animate_service_status)

    def start_transcription(self):

        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showinfo("Info", "Transcription already in progress.")
            return
        
        """Processes only 'In Queue' files and updates statuses in real-time."""
        directory = self.dir_var.get()
        if not directory:
            messagebox.showerror("Error", "Please select a directory first.")
            return

         # No audio files in the queue
        if self.listbox_queue.size() == 0:
            messagebox.showerror("Error", "There are no compatible audio files in the selected directory.")
            return
        
        # All files are already marked Completed
        all_completed = all(self.status_queue.get(i) == "Completed" for i in range(self.status_queue.size()))
        if all_completed:
            messagebox.showinfo("Info", "All audio files have transcribed successfully.")
            return
        
        # Reset the stop flag
        self.stop_requested = False  

        # Start status animation
        self.status_animation_running = True
        self.status_animation_index = 0
        self.animate_service_status()

        self.transcribe_thread = threading.Thread(target=self.transcribe_files, daemon=True)
        self.transcribe_thread.start()


    def transcribe_files(self):
        directory = self.dir_var.get()

        model_name = self.model_var.get()
        language = self.lang_var.get()
        model = whisper.load_model(model_name)

        any_transcribed = False  # Flag to track if any files were processed

        for i in range(self.listbox_queue.size()):
            
            if self.stop_requested:
                self.status_animation_running = False
                self.service_status.config(text="Service is currently Stopped")
                messagebox.showinfo("Stopped", "The Active Transcriber Service has been stopped.")
                return  # Exit early
            
            
            filename = self.listbox_queue.get(i)
            status = self.status_queue.get(i)

            # Only process files marked as 'In Queue'
            if status == "In Queue":
                file_path = os.path.join(directory, filename)
                output_file = os.path.join(directory, f"{os.path.splitext(filename)[0]}.txt")

                # Update status to "Processing..."
                self.status_queue.delete(i)
                self.status_queue.insert(i, "Processing...")
                self.root.update_idletasks()

                try:
                    # Transcribe audio
                    result = model.transcribe(file_path, language=language)

                    # Save transcription
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(result["text"])

                    # Update status to "Completed"
                    self.status_queue.delete(i)
                    self.status_queue.insert(i, "Completed")

                    any_transcribed = True # Mark as transcribed

                except Exception as e:
                    #If transcription fails, mark as "Error"
                    self.status_queue.delete(i)
                    self.status_queue.insert(i, "Error")
        if any_transcribed:
            self.status_animation_running = False
            self.service_status.config(text="Service is currently Stopped")
            messagebox.showinfo("Success", "All audio files have been successfully transcribed!")
            
    def on_select_file(self, event):
        """Populate output_box with transcription or placeholder message based on status."""
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
        else:
            self.output_box.insert(tk.END, "No Transcription Detected")

        self.output_box.config(state="disabled")

# Run the application
if __name__ == "__main__":
    
    if not check_ffmpeg():
        exit()  # Abort launch if ffmpeg is not found
    
    root = ttk.Window(themename="darkly")
    app = TranscribeAudioService(root)
    root.mainloop()
