# File: gui/ui_main.py

import os
import threading
import tkinter as tk
import time
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import ttkbootstrap as ttk
import shutil
from gui.settings_input import SettingsInputFrame
from gui.settings_output import SettingsOutputFrame
from gui.settings_model import SettingsModelFrame
from gui.queue_display import QueueFrame
from gui.service_controls import ServiceControlsFrame

from gui.style_config import get_theme_style, get_bootstyles

import tempfile

from services.transcription import transcribe_file,transcribe_file_with_diarization, list_audio_files
from services.utils_transcribe import save_transcript, get_lang_name, get_device_status, qualifies_for_batch_processing, get_optimal_batch_size
from services.version import __version__

from services.template_manager import TemplateManager


class TranscribeApp:
    def __init__(self, root):
        self.root = root
        self._configure_root_window()

        # Load global style and font
        self.style, self.icon_font, self.label_font = get_theme_style()
        self.styles = get_bootstyles()

        # Global state variables
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.model_var = ttk.StringVar(value="medium")
        self.lang_var = ttk.StringVar(value="en")
       
        self.output_format_var = tk.StringVar(value="txt")

        self.speaker_recognition_var = tk.BooleanVar(value=False)
        self.monitoring_enabled_var = tk.BooleanVar(value=False)
        self.monitoring_interval_var = tk.IntVar(value=300) 
        self.translate_var = tk.BooleanVar(value=False)

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
        self.root.geometry("1000x700")
        self.root.resizable(False, False) 

    def _build_ui(self):
        # Row 0 — Input + Output Settings side by side
        # Create wrapper for Input + Output Settings
        self.Settings_In_Out_Wrapper = ttk.Frame(self.root)
        self.Settings_In_Out_Wrapper.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Ensure both columns in the wrapper expand equally
        self.Settings_In_Out_Wrapper.columnconfigure(0, weight=1)
        self.Settings_In_Out_Wrapper.columnconfigure(1, weight=1)

        # Input Settings Frame (LEFT)
        self.input_settings = SettingsInputFrame(
            self.Settings_In_Out_Wrapper,
            input_dir_var=self.input_dir_var,
            language_var=self.lang_var,
            monitoring_enabled_var=self.monitoring_enabled_var,
            monitoring_interval_var=self.monitoring_interval_var,
            styles=self.styles,
            label_font=self.label_font,
            browse_callback=self.browse_input_directory
        )
        self.input_settings.grid(row=0, column=0, padx=5, pady=2, sticky="nsew")

        # Output Settings Frame (RIGHT)
        self.output_settings = SettingsOutputFrame(
            self.Settings_In_Out_Wrapper,
            output_dir_var=self.output_dir_var,
            output_format_var=self.output_format_var,
            translate_var=self.translate_var,
            language_var=self.lang_var,
            styles=self.styles,
            label_font=self.label_font,
            on_format_change=self.on_output_format_change,
            browse_callback=self.browse_output_directory
        )
        self.output_settings.grid(row=0, column=1, padx=5, pady=2, sticky="nsew")

        # Connects Input / Output Validation logic
        self.input_settings.set_output_frame(self.output_settings)

        
        #Model Settings (centered by columnspan)
        self.model_settings = SettingsModelFrame(
            self.root,
            speaker_recognition_var=self.speaker_recognition_var,
            styles=self.styles,
            label_font=self.label_font
        )
        self.model_settings.grid(row=1, column=0, columnspan=2, padx=5, pady=(5, 10), sticky="n")

        #Queue and Output Display
        self.queue_frame = QueueFrame(
            self.root,
            self.on_select_file,
            self.on_double_click_file,
            self.refresh_directory,
            styles=self.styles
        )
        self.queue_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.listbox_queue, self.status_queue, self.output_box = self.queue_frame.get_queue_widgets()

        # Row 3 — Service Controls
        self.service_controls = ServiceControlsFrame(
            self.root,
            self.start_transcription,
            self.stop_transcription,
            styles=self.styles
        )
        self.service_controls.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="w")

        self.service_status = self.service_controls.get_status_label()


    # ────────────────────────────────────────────────
    # Helper Methods
    # ────────────────────────────────────────────────

    def set_ui_inputs_state(self, enabled: bool):
        # Prevent enabling the UI if we are in idle monitoring mode
        if enabled and getattr(self, "idle_mode", False):
            return

        state = "normal" if enabled else "disabled"

        self.input_settings.set_state(state)
        self.output_settings.set_state(state)
        self.model_settings.set_state(state)


    def browse_input_directory(self):
        
        directory = filedialog.askdirectory()

        if directory:
            # Set input directory
            self.input_dir_var.set(directory)
            # Auto-assign output directory
            self.output_dir_var.set(directory)
            # Notify user
            messagebox.showinfo(
                "Output Directory Set",
                f"Output Directory has been automatically assigned a value of:\n\n{directory}"
            )

            # Refresh the transcribe queue
            self.populate_queue(self.input_dir,self.output_dir)

    def browse_output_directory(self):
        
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
            # Refresh the transcribe queue
            self.populate_queue(self.input_dir,self.output_dir)


    def continuous_monitoring(self):
        """
        Enters idle state between transcription cycles and schedules the next run.
        """
        if self.stop_requested:
            return

        self.status_animation_running = True
        self.status_animation_index = 0
        self.idle_mode = True  
        self.animate_service_status()

        self.set_ui_inputs_state(False)

        interval_ms = self.monitoring_interval * 200
        self.monitor_after_id = self.root.after(interval_ms, self._run_monitor_cycle)


    def _run_monitor_cycle(self):
        if self.stop_requested:
          
            return  # Prevent restarting if Stop was clicked during wait period
    
        self.refresh_directory()
        self.start_transcription()


    def refresh_directory(self):
        if not self.input_dir:
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
        self.populate_queue(self.input_dir,self.output_dir)

    def populate_queue(self, input_directory, output_directory):
        self.audio_files = list_audio_files(input_directory)
        self.listbox_queue.delete(0, tk.END)
        self.status_queue.delete(0, tk.END)
        for file in self.audio_files:
            transcript_path = os.path.join(output_directory, f"{os.path.splitext(file)[0]}.{self.output_extension}")
            status = "Completed" if os.path.exists(transcript_path) else "In Queue"
            self.listbox_queue.insert(tk.END, file)
            self.status_queue.insert(tk.END, status)

    def start_transcription(self):
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showinfo("Info", "Transcription already in progress.")
            return

        if not self.input_dir:
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
        self.idle_mode = False 
        self.status_animation_running = True
        self.status_animation_index = 0
        self.set_ui_inputs_state(False)
        self.animate_service_status()
        self.transcribe_thread = threading.Thread(target=self.transcribe_files, daemon=True)
        self.transcribe_thread.start()

    def transcribe_files(self):
        any_transcribed = False

        #Start Service Timer
        self.service_controls.start_time = time.time()
        self.service_controls.update_service_timer()

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

            file_path = os.path.join(self.input_dir, filename)
            output_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}.{self.output_extension}")

            # Batch size qualifier start
            qualifies_for_batch = qualifies_for_batch_processing(file_path, self.use_diarization)
            if qualifies_for_batch:
                vram_gb = self.model_settings._get_available_vram()
                batch_size = get_optimal_batch_size(vram_gb, self.gpu_available)
            else:
                batch_size = 1
            # Batch size qualifier end

            self.status_queue.delete(i)
            self.status_queue.insert(i, "Processing...")
            self.root.update_idletasks()
            self.start_processing_animation(i)
            
            # Inside your transcription trigger logic in ui_main.py
            temp_dir = tempfile.mkdtemp(prefix="transcribe_job_")

            try:
                if self.use_diarization:
                    result = transcribe_file_with_diarization(
                        file_path,
                        temp_dir=temp_dir, 
                        model_name=self.model,
                        language=self.language,
                        translate_to_english=self.translate_to_english,
                        
                    )
                else:
                    result = transcribe_file(
                        file_path,
                        temp_dir, 
                        self.model,
                        self.language,
                        return_segments=False,
                        translate_to_english=self.translate_to_english,
                    )
            finally:
                # 🧼 Cleanup temp directory and all files inside it
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

            if "text" in result:
                try:
                    save_transcript(
                        output_path,
                        result["text"],
                        self.active_template,
                        input_file=file_path,
                        input_language=get_lang_name(self.language),
                        output_language="English" if self.translate_to_english else get_lang_name(self.language),
                        model_used=self.model,
                        processing_device="GPU" if self.gpu_available else "CPU",
                        batch_size=batch_size,
                        use_diarization=self.use_diarization,
                        output_format=self.output_extension
                    )
                    self.stop_processing_animation()
                    self.status_queue.delete(i)
                    self.status_queue.insert(i, "Completed")
                    any_transcribed = True
                except Exception as e:
                    self.stop_processing_animation()
                    self.status_queue.delete(i)
                    self.status_queue.insert(i, "Error")
                    self.error_messages[filename] = f"Failed to save transcript: {str(e)}"
            else:
                self.stop_processing_animation()
                self.status_queue.delete(i)
                self.status_queue.insert(i, "Error")
                self.error_messages[filename] = result.get("error", "Unknown error")
            
        #End Service Timer
        self.service_controls.stop_service_timer()

        # All transcription is now done — finalize state
        self.status_animation_running = False
        self.set_ui_inputs_state(True)

        #Stop condition takes precedence
        if self.stop_requested:
            self.service_status.config(text="Service is currently Stopped")
            self.stop_requested = False  # Optional: reset flag
        elif self.monitoring_enabled:
            self.continuous_monitoring()
        elif any_transcribed:
            messagebox.showinfo("Success", "All audio files have been transcribed.")
            self.service_status.config(text="Service is currently Stopped")
        else:
            self.service_status.config(text="Service is currently Stopped")


    def stop_transcription(self):
        if (self.transcribe_thread and self.transcribe_thread.is_alive()) or getattr(self, "idle_mode", False):
            self.stop_requested = True

            if hasattr(self, "monitor_after_id"):
                self.root.after_cancel(self.monitor_after_id)

            #End Service Timer
            self.service_controls.stop_service_timer()

            # 🟢 Don't stop animation — let it run during the final transcription
            self.idle_mode = False
            self.status_animation_running = True
            self.status_animation_index = 0
            self.animate_service_status()

            
        else:
            messagebox.showinfo("Info", "Transcription service is not running.")

    
    def on_double_click_file(self, event):
        selection = event.widget.curselection() # event.widget is a tk.Listbox at runtime, not recognized in VS code
        if not selection:
            return

        index = selection[0]
        filename = self.listbox_queue.get(index)
        status = self.status_queue.get(index)
        transcript_path = os.path.join(self.input_dir, f"{os.path.splitext(filename)[0]}.{self.output_extension}")

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
        transcript_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}.{self.output_extension}")

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

        if self.stop_requested:
            self.service_status.config(text=f"Processing Stop Request{dots}")
        elif getattr(self, "idle_mode", False):
            self.service_status.config(text=f"Service is currently idle{dots}")
        else:
            self.service_status.config(text=f"Service is currently running{dots}")

        self.status_animation_index += 1
        self.root.after(500, self.animate_service_status)

    def on_output_format_change(self, *args):
        if not self.input_dir:
            return
        self.refresh_directory()
        messagebox.showinfo(
            "Output Format Changed",
            "The output format has been updated.\nThe queue has been refreshed."
            )


    #File processing ... animation methods    
    def start_processing_animation(self, row_index):
        self.processing_animation_running = True
        self.processing_row_index = row_index  # 👈 track which row we're animating
        self.processing_dots = 0

        def animate():
            if not self.processing_animation_running:
                return
            if self.processing_row_index >= self.status_queue.size():
                return  #  end early if out of range
            dots = "." * (self.processing_dots % 4)
            current_text = f"Processing{dots}"
            try:
                self.status_queue.delete(self.processing_row_index)
                self.status_queue.insert(self.processing_row_index, current_text)
            except Exception:
                return  # Row may no longer exist (edge case)

            self.processing_dots += 1
            self.root.after(500, animate)

        animate()

    def stop_processing_animation(self):
        self.processing_animation_running = False

    # ────────────────────────────────────────────────
    # UI Property Accessors
    # ────────────────────────────────────────────────

    @property
    def input_dir(self):
        return self.input_dir_var.get()
    
    @property
    def output_dir(self):
        return self.output_dir_var.get()

    @property
    def model(self):
        return self.model_settings.get_selected_model(lang_code=self.language)

    @property
    def language(self):
        return self.lang_var.get()

    @property
    def output_extension(self):
        return self.output_format_var.get()

    @property
    def use_diarization(self):
        return self.speaker_recognition_var.get()
    @property
    def monitoring_enabled(self):
        return self.monitoring_enabled_var.get()

    @property
    def monitoring_interval(self):
        return self.monitoring_interval_var.get()
    
    @property
    def translate_to_english(self):
        return self.translate_var.get() 
    
    # ────────────────────────────────────────────────
    # Device Property Accessors
    # ────────────────────────────────────────────────

    @property
    def gpu_available(self):
        _, available = get_device_status()
        return available

    @property
    def device_name(self):
        name, _ = get_device_status()
        return name