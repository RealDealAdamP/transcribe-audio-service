# File: transcribe_audio_service/services/utils_debug.py

import os
import time
import pandas as pd
from contextlib import contextmanager
from cfg.conf_debug import DEBUG_DATA_TRANS  # Make sure this import is valid

@contextmanager
def stage_timer(stage_name, update_callback=None):
    start_time = time.time()
    print(f"⏳ Starting: {stage_name}...")
    if update_callback:
        update_callback(f"⏳ Starting {stage_name}...")
    yield
    duration = time.time() - start_time
    print(f"✅ Completed: {stage_name} in {duration:.2f} seconds")
    if update_callback:
        update_callback(f"✅ Completed: {stage_name} in {duration:.2f} sec")



def export_debug_csv(df, flag_key):
    """
    Exports a DataFrame as a timestamped CSV file if the associated debug flag is enabled.

    Args:
        df (pd.DataFrame): The data to export.
        flag_key (str): Also used as filename stem and config key to check in DEBUG_DATA_TRANS.
    """
    if not DEBUG_DATA_TRANS.get(flag_key, False):
        return

    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{flag_key}_{timestamp}.csv"
        output_dir = DEBUG_DATA_TRANS.get("output_dir", "./debug_dumps/")
        os.makedirs(output_dir, exist_ok=True)

        full_path = os.path.join(output_dir, filename)
        df.to_csv(full_path, index=False, float_format="%.8f")

        print(f"📤 [DEBUG] Exported: {full_path}")
    except Exception as e:
        print(f"❌ Failed to export debug CSV for {flag_key}: {e}")
