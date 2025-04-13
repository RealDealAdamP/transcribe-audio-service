# File: gui/ui_main.py

import os
import threading
import tkinter as tk
import time
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
import shutil
from gui.settings_input import SettingsInputFrame
from gui.settings_output import SettingsOutputFrame
from gui.settings_model import SettingsModelFrame
from gui.queue_display import QueueFrame
from gui.service_controls import ServiceControlsFrame
from gui.device_monitor import DeviceMonitorFrame
import pandas as pd
from pathlib import Path
from cfg.conf_style import get_theme_style, get_bootstyles
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import tempfile
from services.utils_models import find_new_seg_id
from services.utils_audio import list_audio_files, prep_whisper_audio
from services.utils_device import  get_device_status, get_optimal_batch_size
from services.utils_transcribe import save_transcript, get_lang_name, qualifies_for_batch_processing,transcribe_file
from services.utils_diarize import run_diarization_pipeline
from services.utils_output import load_output_file, save_cluster_data
from services.version import __version__
from services.template_manager import TemplateManager


class TranscribeApp:
    def __init__(self, root, on_ready=None):
        self.root = root

        # Load global style and font
        self.style, self.fonts = get_theme_style()
        self.styles = get_bootstyles()

        # Global state variables
        self.diagnostics_enabled = True
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.model_var = ttk.StringVar(value="medium")
        self.lang_var = ttk.StringVar(value="en")
        self.output_format_var = tk.StringVar(value="txt")

        self.speaker_identification_var = tk.BooleanVar(value=False)
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
            label_font=self.fonts["label"],        
            browse_callback=self.browse_input_directory,
            view_callback=self.view_input_directory
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
            label_font=self.fonts["label"],
            on_format_change=self.on_output_format_change,
            browse_callback=self.browse_output_directory,
            view_callback=self.view_output_directory
        )
        self.output_settings.grid(row=0, column=1, padx=5, pady=2, sticky="nsew")

        # Connects Input / Output Validation logic
        self.input_settings.set_output_frame(self.output_settings)
        #Force initial dropdown filtering to match checkbox state
        
        # Row 1 — Model Settings + Device Monitor side by side
        self.Model_Monitor_Wrapper = ttk.Frame(self.root)
        self.Model_Monitor_Wrapper.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=(5, 10))

        self.Model_Monitor_Wrapper.columnconfigure(0, weight=1)
        self.Model_Monitor_Wrapper.columnconfigure(1, weight=1)

        # Model Settings Frame (LEFT)
        self.model_settings = SettingsModelFrame(
            self.Model_Monitor_Wrapper,
            speaker_identification_var=self.speaker_identification_var,
            styles=self.styles,
            label_font=self.fonts["label"]
        )
        self.model_settings.grid(row=0, column=0, padx=5, pady=2, sticky="nsew")

        # Device Monitor Frame (RIGHT)
        self.device_monitor = DeviceMonitorFrame(
            self.Model_Monitor_Wrapper,
            styles=self.styles
        )
        self.device_monitor.grid(row=0, column=1, padx=5, pady=2, sticky="nsew")

        #Queue and Output Display
        self.queue_frame = QueueFrame(
            self.root,
            self.on_select_file,
            self.on_double_click_file,
            on_refresh_click=self.refresh_directory,    # 👈 pass refresh handler
            on_reset_queue=self.que_reset,    
            styles=self.styles
        )
        self.queue_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.listbox_queue, self.status_queue, self.output_box = self.queue_frame.get_queue_widgets()

        # Service Controls
        self.service_controls = ServiceControlsFrame(
            self.root,
            self.start_transcription,
            self.stop_transcription,
            styles=self.styles
        )
        self.service_controls.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="w")

        self.service_status = self.service_controls.get_status_label()

        self.set_scroll_bar_h_viz()

    # ────────────────────────────────────────────────
    # Helper Methods
    # ────────────────────────────────────────────────

    def initialize_ui(self):
        self._build_ui()

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
            
            # Only refresh queue if input_dir is set and exists
            input_dir = self.input_dir_var.get()
            if input_dir and os.path.isdir(input_dir):
                self.populate_queue(input_dir, directory)


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

        # Re-populate queue
        self.populate_queue(self.input_dir, self.output_dir)

    def que_reset(self):
        """
        Deletes output files in the output directory that match the base names of 
        input audio files and use the currently selected output extension only.
        """

        if not self.input_dir:
            messagebox.showerror("Error", "Cannot reset empty queue.")
            return
        if self.transcribe_thread and self.transcribe_thread.is_alive():
            messagebox.showerror("Error", "Cannot reset while queue is active.")
            return
        
        # Valid audio extensions
        audio_exts = (".mp3", ".wav", ".m4a", ".wma", ".flac", ".ogg", ".aac")

        # Get base names from input audio files
        input_basenames = {
            os.path.splitext(f)[0]
            for f in os.listdir(self.input_dir)
            if f.lower().endswith(audio_exts)
        }

        # Normalize extension (e.g., "txt" -> ".txt")
        target_ext = f".{self.output_extension.lstrip('.')}".lower()
        deleted_files = []

        for file_name in os.listdir(self.output_dir):
            base, ext = os.path.splitext(file_name)
            if ext.lower() == target_ext and base in input_basenames:
                try:
                    full_path = os.path.join(self.output_dir, file_name)
                    os.remove(full_path)
                    deleted_files.append(file_name)
                except Exception as e:
                    print(f"Failed to delete {file_name}: {e}")

        # Show results
        msg = f"Deleted {len(deleted_files)} directory output file(s)."
        if deleted_files:
            msg += "\n\n" + "\n".join(deleted_files[:10])
            if len(deleted_files) > 10:
                msg += "\n..."

        messagebox.showinfo("Directory Cleanup 🧹", msg)
        self.refresh_directory()


    def populate_queue(self, input_directory, output_directory):
        self.audio_files = list_audio_files(input_directory)
        self.listbox_queue.delete(0, tk.END)
        self.status_queue.delete(0, tk.END)
        
        cluster_dir = Path("cluster_data")
        
        for file in self.audio_files:
            
            transcript_path = os.path.join(output_directory, f"{os.path.splitext(file)[0]}.{self.output_extension}")
            status = "Completed" if os.path.exists(transcript_path) else "In Queue"

            #Feather cleanup logic (only for non-complete entries)
            if status != "Completed":
                stem = Path(file).stem
                cluster_file = cluster_dir / f"{stem}_umap.feather"
                if cluster_file.exists():
                    try:
                        cluster_file.unlink()
                        print(f"🧹 Removed stale cluster data → {cluster_file}")
                    except Exception as e:
                        print(f"⚠️ Could not remove {cluster_file}: {e}")


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
        self.transcribe_thread = threading.Thread(target=self.run_transcription, daemon=True)
        self.transcribe_thread.start()

    def run_transcription(self):
        any_transcribed = False

        # Start Service Timer
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

            # Batch size qualifier
            qualifies_for_batch = qualifies_for_batch_processing(file_path, self.use_diarization)
            if qualifies_for_batch:
                vram_gb = self.model_settings._get_available_vram()
                batch_size = get_optimal_batch_size(vram_gb, self.gpu_available)
            else:
                batch_size = 1

            self.status_queue.delete(i)
            self.status_queue.insert(i, "Processing...")
            self.root.update_idletasks()
            self.start_processing_animation(i)

            temp_dir = tempfile.mkdtemp(prefix="transcribe_job_")
            audio_mp3_path = prep_whisper_audio(file_path, temp_dir)

            try:
                result = transcribe_file(
                    audio_mp3_path,
                    model_name=self.model,
                    language=self.language,
                    translate_to_english=self.translate_to_english
                )
                
                # Merge segments *before* passing to diarization pipeline
                segments = result.get("segments", [])
                # 🐞 Optional: dump segments for debug
                pd.DataFrame(segments).to_csv(r"C:\demo\get_whisper_segments.csv", index=False, float_format="%.8f")

                if segments:
                    merged_segments = find_new_seg_id(segments)
                    result["segments"] = merged_segments  # overwrite with cleaned segments
                    
                    
                if self.use_diarization:

                    # Only trigger cluster Animation status if this file is selected in UI
                    selection = self.listbox_queue.curselection()
                    is_selected = selection and self.listbox_queue.get(selection[0]) == filename
                    ui_callback = self.queue_frame.set_cluster_status if is_selected else None

                    diarization_result = run_diarization_pipeline(
                        audio_mp3_path,
                        result["segments"],
                        diagnostics=True,
                        ui_callback = ui_callback
                    )
    
                   # Step 1: Overwrite final speaker-labeled segments
                    result["segments"] = diarization_result["segments"]
                    pd.DataFrame(result["segments"]).to_csv(r"C:\demo\get_post_diarize_segments.csv", index=False, float_format="%.8f")



                    # Step 2: Save cluster data to file (for UI scatter plot)
                    cluster_df = diarization_result.get("cluster_data")
                    if cluster_df is not None:
                        
                        save_cluster_data(
                            df=cluster_df,
                            filename=filename        # must be the original input file, not temp mp3
                                
                        )

                    # Step 3: Optional diagnostic printout (for dev mode)
                    if self.diagnostics_enabled:
                        diagnostics = diarization_result.get("diagnostics", {})
                        for stage, summary_df in diagnostics.items():
                            print(f"\n📊 Speaker Summary at stage: {stage}")
                            print(summary_df)

                                            
            except Exception as e:
                print(f"❌ Transcription or Librosa Diarization failed: {e}")
                self.status_queue.delete(i)
                self.status_queue.insert(i, "Error")

            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

            try:

                save_transcript(
                    output_path,
                    result,
                    self.active_template,
                    input_file=file_path,
                    input_language=get_lang_name(self.language),
                    output_language="English" if self.translate_to_english else get_lang_name(self.language),
                    model_used=self.model,
                    processing_device="GPU" if self.gpu_available else "CPU",
                    batch_size=batch_size,
                    use_diarization=self.use_diarization,
                    output_format=self.output_extension,
                )

                self.stop_processing_animation()
                self.status_queue.delete(i)
                self.status_queue.insert(i, "Completed")
                any_transcribed = True

                # 🧠 Check if this is the currently selected file
                current_selection = self.listbox_queue.curselection()
                if current_selection and self.listbox_queue.get(current_selection[0]) == filename:
                    self.queue_frame.display_cluster_plot(filename)

            except Exception as e:
                self.stop_processing_animation()
                self.status_queue.delete(i)
                self.status_queue.insert(i, "Error")
                self.error_messages[filename] = f"Failed to save transcript: {str(e)}"

        # End Service Timer
        self.service_controls.stop_service_timer()

        self.status_animation_running = False
        self.set_ui_inputs_state(True)

        if self.stop_requested:
            self.service_status.config(text="Service is currently Stopped")
            self.stop_requested = False
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
        selection = event.widget.curselection()
        if not selection:
            return

        index = selection[0]
        filename = self.listbox_queue.get(index)
        status = self.status_queue.get(index)
        transcript_path = os.path.join(self.output_dir, f"{os.path.splitext(filename)[0]}.{self.output_extension}")

        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)

        # Final display logic centralized here
        if status == "Completed" and os.path.exists(transcript_path):
            output_text = load_output_file(transcript_path)
            self.output_box.insert(tk.END, output_text)
            self.queue_frame.display_cluster_plot(filename)

        elif status == "Error":
            error_msg = self.error_messages.get(filename, "An unknown error occurred.")
            self.output_box.insert(tk.END, f"Transcription Error:\n{error_msg}")
            self.queue_frame.set_cluster_status("❌ No Cluster Data Available")

        elif status == "Processing...":
            self.output_box.insert(tk.END, "File is currently being processed...")
            self.queue_frame.set_cluster_status("⏳ Cluster Data Loading", animate=True)

        else:
            self.output_box.insert(tk.END, "No Transcription Detected")
            self.queue_frame.set_cluster_status("❌ No Cluster Data Available")

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

        # 🔁 Update scroll behavior based on new format
        self.set_scroll_bar_h_viz()

        # 🔃 Refresh queue display
        self.refresh_directory()

        # ℹ️ Notify user
        messagebox.showinfo(
            "Output Format Changed",
            "The output format has been updated.\nThe queue has been refreshed."
        )


    #File processing ... animation methods    
    def start_processing_animation(self, row_index):
        self.processing_animation_running = True
        self.processing_row_index = row_index
        self.processing_dots = 0

    

        def animate():
            if not self.processing_animation_running:
                return
            if self.processing_row_index >= self.status_queue.size():
                return

            dots = "." * (self.processing_dots % 4)
            current_text = f"Processing{dots}"
            try:
                self.status_queue.delete(self.processing_row_index)
                self.status_queue.insert(self.processing_row_index, current_text)
            except Exception:
                return

            self.processing_dots += 1
            self.root.after(500, animate)

        animate()

    def stop_processing_animation(self):
        self.processing_animation_running = False



    def set_scroll_bar_h_viz(self):
        is_horizontal = self.output_extension.lower() in ("parquet", "csv")
        self.queue_frame.configure_output_display(
            wrap_mode="none" if is_horizontal else "word",
            use_horizontal_scroll=is_horizontal
        )

    def view_input_directory(self):
                directory = self.input_dir_var.get()
                if not directory or not os.path.isdir(directory):
                    messagebox.showinfo("No Directory Selected", "Please select a valid input directory first.")
                    return

                try:
                    os.startfile(directory)  # Windows only
                except Exception as e:
                    messagebox.showerror("Error Opening Directory", str(e))

    def view_output_directory(self):
        directory = self.output_dir_var.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showinfo("No Directory Selected", "Please select a valid output directory first.")
            return

        try:
            os.startfile(directory)  # Windows only
        except Exception as e:
            messagebox.showerror("Error Opening Directory", str(e))

     

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
        return self.speaker_identification_var.get()
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