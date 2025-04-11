# File: transcribe_audio_service/services/utils_diarize.py

import librosa 
import torch
from silero_vad import load_silero_vad, get_speech_timestamps
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler, StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from pandas.api.types import is_numeric_dtype
import hdbscan
import scipy.stats
import time
from concurrent.futures import ThreadPoolExecutor
import umap
from pathlib import Path
import os
from services.utils_perf import stage_timer
from typing import Union


def run_diarization_pipeline(audio_path, whisper_segments, return_summary_only=False, diagnostics=True):
    diagnostics_snapshots = {}
    

    with stage_timer("✅ Loading Audio Stage"):
        # Load original audio
        y, sr = librosa.load(audio_path, sr=16000, mono=True)

    with stage_timer("✅ Detect Voice Segments Stage"):

        # Extract only voiced parts
        speech_timestamps, is_voiced = detect_voice_segments(y, sr=sr, return_mask=True)
        
        # Get frame_times BEFORE any filtering
        frame_times = librosa.frames_to_time(np.arange(len(is_voiced)), sr=sr, hop_length=160)
       
        # 🐞 Debug dump: frame index + time
        frame_debug_df = pd.DataFrame({
            "frame_index": np.arange(len(frame_times)),
            "frame_time": frame_times
        })
        
        frame_debug_df.to_csv(r"C:\demo\frame_times.csv", index=False)

    with stage_timer("✅ Feature Extraction Stage"):
        # Step 1: Extract Librosa features (frame-level)
        identify_audio_df = run_librosa_identification(y, sr=sr, is_voiced=is_voiced, frame_times=frame_times,log_power=2)

        identify_audio_df.to_csv(r"C:\demo\normalize_input.csv", index=False)
    with stage_timer("✅ Feature Normalization Stage"):
        # Step 2: Normalize featuers
        identify_audio_df = normalize_audio_features(identify_audio_df, scale=True, scale_type="zscore")

        identify_audio_df.to_csv(r"C:\demo\normalize_output.csv", index=False)
    with stage_timer("✅ Segment Tagging Stage"):
        #Setp 3 tag_frames_with_segments
        identify_audio_df = tag_frames_with_segments(identify_audio_df, whisper_segments)
    print()


    with stage_timer("✅ Time Aggregation Stage"):    
        #Step 4 apply time aggregation by second
        data_for_clustering = apply_time_agg(identify_audio_df,bin_size=1)

        

    with stage_timer("✅ Feature Clustering Stage"):
        # Step 5: Perform clustering via HDBSCAN & UMAP on selected data
        clustered_df, speaker_summary = cluster_full_features(
            data_for_clustering,
            use_umap=True,
            min_cluster_size=max(5, int(0.02 * len(data_for_clustering))),
            min_samples=max(2, int(0.01 * len(data_for_clustering)))
        )

    clustered_df.to_csv(r"C:\demo\cluster_df_output.csv", index=False)
   

    if diagnostics:
        diagnostics_snapshots["frame_level_clustering"] = speaker_summary

    # Step 4: Map speaker labels back to Whisper segments
    labeled_segments = assign_speakers_to_segments(clustered_df, whisper_segments)

    # Step 5: Final output
    result = {
        "segments": labeled_segments,  # speaker-labeled Whisper segments
        "cluster_data": clustered_df[["x", "y", "speaker_id"]].copy()
    }


    if diagnostics:
        result["diagnostics"] = diagnostics_snapshots

    return result


# ────────────────────────────────────────────────
# Diarization Pipeline Stage Methods
# ────────────────────────────────────────────────

def detect_voice_segments(
    y,
    sr=16000,
    hop_length=160,
    threshold=0.5,
    min_speech_duration_ms=250,
    max_speech_duration_s=15,
    return_mask=True
):
    try:
        model = load_silero_vad()
        print("✅ Silero VAD model loaded (direct import)")
    except Exception as e:
        print("❌ ERROR: Failed to load Silero VAD model")
        raise e

    # 📡 Get VAD timestamps
    audio_tensor = torch.FloatTensor(y)
    speech_timestamps = get_speech_timestamps(
        audio_tensor,
        model,
        sampling_rate=sr,
        threshold=threshold,
        min_speech_duration_ms=min_speech_duration_ms,
        max_speech_duration_s=max_speech_duration_s,
        return_seconds=True
    )
    

    if not speech_timestamps:
        raise ValueError("VAD did not detect any voiced segments in the input audio.")

    print(f"🗣️ Detected {len(speech_timestamps)} voiced segments")

    if return_mask:
        n_frames = int(np.ceil(len(y) / hop_length))
        frame_voiced = np.zeros(n_frames, dtype=bool)
        for ts in speech_timestamps:
            start_idx = int(np.floor(ts['start'] * sr / hop_length))
            end_idx = int(np.ceil(ts['end'] * sr / hop_length))
            frame_voiced[start_idx:end_idx + 1] = True
        
            # 📤 Export speech_timestamps to CSV
        pd.DataFrame(speech_timestamps).to_csv(r"C:\demo\vad_segments.csv", index=False)

        # 📤 Export frame_voiced mask to CSV (with index for reference)
        pd.DataFrame({
            "frame_index": np.arange(n_frames),
            "is_voiced": frame_voiced.astype(int)  # Convert to 0/1 for readability
        }).to_csv(r"C:\demo\vad_mask.csv", index=False)

        return speech_timestamps, frame_voiced

    return speech_timestamps



def run_librosa_identification(
    y,
    sr=16000,
    hop_length=160,
    is_voiced=None,
    frame_times=None,
    n_fft=512,
    n_mfcc=25,
    n_mels=40,
    fmax=4000,
    log_power=1  # 💡 New: log power exponent (1 = normal, >1 = emphasized, <1 = disallowed)
):

    timings = {}

    if log_power < 1:
        raise ValueError("log_power must be >= 1 for meaningful feature extraction.")

    # 🎛️ Step 1: MFCCs, Delta MFCCs, DDelta MFCCs
    t0 = time.time()
    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=n_fft, hop_length=hop_length,
        n_mels=n_mels, fmax=fmax
    )

    # 🔊 Apply optional log power adjustment
    mel_spec_powered = np.power(mel_spec, log_power)
    mfcc = librosa.feature.mfcc(S=librosa.power_to_db(mel_spec_powered), n_mfcc=n_mfcc)
    timings["mfcc"] = time.time() - t0

    # 🎚️ Δ MFCCs
    t1 = time.time()
    delta_mfcc = librosa.feature.delta(mfcc)
    timings["delta_mfcc"] = time.time() - t1

    # 🎚️ ΔΔ MFCCs
    t2 = time.time()
    ddelta_mfcc = librosa.feature.delta(mfcc, order=2)
    timings["ddelta_mfcc"] = time.time() - t2

    # ✅ Set frame count
    if frame_times is None:
        print(f"mel_spec shape: {mel_spec.shape}")
        print(f"mfcc shape: {mfcc.shape}")

        n_frames = mfcc.shape[1]
        
        if n_frames == 0:
            raise ValueError("MFCC returned zero frames — possible issue with mel_spec or audio input.")

        frame_times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop_length)
    else:
        n_frames = len(frame_times)

    debug_df = pd.DataFrame({
        "frame_index": np.arange(len(is_voiced)),
        "is_voiced": is_voiced.astype(int),
        "frame_time": frame_times[:len(is_voiced)]  # Safe slice in case mismatch
    })
    debug_df.to_csv(r"C:\demo\debug_lib_vad_mask.csv", index=False)
    print("[DEBUG] VAD mask dumped to CSV")


    # 🧠 Step 2: Run remaining features asynchronously
    results = {}

    def extract_feature(name, fn):
        t_start = time.time()
        result = fn()
        timings[name] = time.time() - t_start
        results[name] = result

    with ThreadPoolExecutor(max_workers=10) as executor:
        #executor.submit(extract_feature,"zcr",lambda: librosa.feature.zero_crossing_rate(y=y, frame_length=n_fft, hop_length=hop_length))
        #executor.submit(extract_feature, "spectral_centroid", lambda: librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft))
        #executor.submit(extract_feature, "spectral_bandwidth", lambda: librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft))
        executor.submit(extract_feature, "spectral_contrast", lambda: librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft))
        #executor.submit(extract_feature, "spectral_flatness", lambda: librosa.feature.spectral_flatness(y=y, hop_length=hop_length, n_fft=n_fft))
        #executor.submit(extract_feature, "spectral_rolloff", lambda: librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft))
        #executor.submit(extract_feature, "rms", lambda: librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length))
        executor.submit(extract_feature, "f0", lambda: librosa.yin(y=y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr, hop_length=hop_length))
        #executor.submit(extract_feature, "chroma", lambda: librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft))

    # 📦 Build feature DataFrame
    df = pd.DataFrame({
        "time": frame_times,
        **{f"mfcc_{i+1}": mfcc[i][:n_frames] for i in range(n_mfcc)},
        **{f"delta_mfcc_{i+1}": delta_mfcc[i][:n_frames] for i in range(n_mfcc)},
        **{f"ddelta_mfcc_{i+1}": ddelta_mfcc[i][:n_frames] for i in range(n_mfcc)},
        #"zcr": results["zcr"][0][:n_frames],
        #"spectral_centroid": results["spectral_centroid"][0][:n_frames],
        #"spectral_bandwidth": results["spectral_bandwidth"][0][:n_frames],
        #"spectral_flatness": results["spectral_flatness"][0][:n_frames],
        #"spectral_rolloff": results["spectral_rolloff"][0][:n_frames],
        #"rms": results["rms"][0][:n_frames],
        "pitch": results["f0"][:n_frames],
        **{f"spectral_contrast_{i+1}": results["spectral_contrast"][i][:n_frames] for i in range(results["spectral_contrast"].shape[0])}
        #**{f"chroma_{i+1}": results["chroma"][i][:n_frames] for i in range(results["chroma"].shape[0])}
    })
 


    # 🧹 Filter by VAD mask
    if isinstance(is_voiced, np.ndarray) and is_voiced.ndim == 1:
        # 🔍 Add both versions for debug dump
        df["is_voiced_raw"] = is_voiced.astype(int)  # 1 = speech, 0 = non-speech
        df["is_voiced"] = is_voiced  # Boolean mask

        # 🧠 Optional debug
        print(f"[DEBUG] VAD mask True count: {np.sum(is_voiced)} / {len(is_voiced)}")

        # 🧪 Dump full (pre-filtered) frame-level debug
        #df.to_csv(r"C:\demo\interview\lib_output_full.csv", index=False)

        # ✅ Filter and return only voiced frames
        df_filtered = df[df["is_voiced"]].reset_index(drop=True)

        # 🧪 Save post-filter CSV
        df_filtered.to_csv(r"C:\demo\interview\lib_output_mask.csv", index=False)
        print(f"[DEBUG] VAD mask applied: {df_filtered.shape[0]} voiced frames retained")

        return df_filtered

    # In case no mask is applied (fallback)
    #df.to_csv(r"C:\demo\interview\lib_output_nomask.csv", index=False)
    return df


def normalize_audio_features(
    df,
    scale=True,
    scale_type="zscore",  # ✅ Gemini recommendation
    zero_handling="replace",  # ✅ Gemini recommendation
    small_constant=1e-6,
    exclude_columns=["time", "is_voiced_raw", "is_voiced"]
):
    normalized_df = df.copy()

    numeric_cols = [
        col for col in df.columns
        if col not in exclude_columns and is_numeric_dtype(df[col])
    ]

    if not scale:
        return normalized_df

    feature_matrix = normalized_df[numeric_cols].values

    # ✅ Replace all-zero rows with a small constant to avoid distortions
    if zero_handling == "replace":
        zero_mask = np.abs(feature_matrix).sum(axis=1) < small_constant
        feature_matrix[zero_mask] = small_constant

    # ✅ Choose scaler based on type
    if scale_type == "robust":
        scaler = RobustScaler()
    elif scale_type == "zscore":
        scaler = StandardScaler()
    else:
        scaler = MinMaxScaler()

    normalized_df[numeric_cols] = scaler.fit_transform(feature_matrix)

    return normalized_df


def apply_time_agg(df, time_col="time", bin_size=1, min_bin_size=1):
    """
    Aggregates frame-level audio features into time-based bins (no segment overlap constraints).

    Parameters:
        df (pd.DataFrame): Frame-level data with time and features.
        time_col (str): Column representing time in seconds.
        bin_size (float): Size of each time bin (0 = return unbinned).
        min_bin_size (int): Minimum number of frames per bin to retain.

    Returns:
        pd.DataFrame: Time-aggregated features with bin time and midpoint.
    """
    df.to_csv(r"C:\demo\interview\agg_input_debug.csv", index=False)

    if bin_size == 0:
        print('bin size 0 caught')
        df.to_csv(r"C:\demo\agg_0_bin_debug.csv", index=False)
        return df

    # ⏱ Create pure time bins (no segment constraint)
    df["time_bin"] = (np.floor(df[time_col] / bin_size) * bin_size).round(6)

    # 🧼 Remove underpopulated bins
    bin_counts = df["time_bin"].value_counts()
    valid_bins = bin_counts[bin_counts >= min_bin_size].index
    df = df[df["time_bin"].isin(valid_bins)].copy()

    if df.empty:
        raise ValueError("Aggregation failed: all bins under min_bin_size.")

    # 🧼 Define features to aggregate (exclude control/meta columns)
    exclude_cols = {
        time_col, "segment_id", "new_segment_id", "is_voiced", "is_voiced_raw", "time_bin"
    }
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    # 🧮 Group by time_bin
    grouped = df.groupby("time_bin")
    features_mean_df = grouped[feature_cols].mean()
    time_midpoint_df = grouped[time_col].mean().rename("time_midpoint")

    # 🆔 Optional: retain dominant segment IDs for metadata reference
    segment_id_df = grouped["segment_id"].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else -1)
    new_segment_id_df = grouped["new_segment_id"].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else -1)

    # 🧩 Combine all parts
    final_df = pd.concat([
        segment_id_df.rename("segment_id"),
        new_segment_id_df.rename("new_segment_id"),
        grouped["time_bin"].first().rename("time"),
        time_midpoint_df,
        features_mean_df
    ], axis=1).reset_index(drop=True)

    final_df = final_df.sort_values("time").reset_index(drop=True)
    final_df.to_csv(r"C:\demo\interview\agg_output_debug.csv", index=False)

    return final_df


def cluster_full_features(
    df,
    min_cluster_size=None,
    min_samples=None,
    confidence_threshold=0.1,
    smooth_labels=True,
    smoothing_window=5,
    use_umap=True,
):

    df.to_csv(r"C:\demo\cluster_feature_matrix_input.csv", index=False)

    exclude = ["time","segment_id", "new_segment_id", "time_midpoint","is_voiced_raw","is_voiced"]
    feature_cols = [col for col in df.columns if col not in exclude]
    
    feature_matrix = df[feature_cols].fillna(0).values

    pd.DataFrame(feature_matrix).to_csv(r"C:\demo\cluster_feature_matrix.csv", index=False)
    
    # Dimensionality reduction (UMAP or passthrough)
    if use_umap:
        umap_params = {
            "n_neighbors": 15,
            "min_dist": 0.1,
            "n_components": 15,
            "metric": "cosine",
            "n_epochs": 200,
            "random_state": 69
        }
        X_cluster = apply_umap(feature_matrix, umap_params)
    else:
        X_cluster = feature_matrix

    n_interval = len(df)  # represents time-binned intervals 

    min_cluster_size = min_cluster_size or max(30, int(0.005 * n_interval))
    min_samples = min_samples or max(10, int(0.001 * n_interval))

    print(f"🧪 Clustering {n_interval} intervals → min_cluster_size={min_cluster_size}, min_samples={min_samples}")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    ).fit(X_cluster)

    labels = clusterer.labels_
    if smooth_labels:
        labels = smooth_labels_fn(labels, window=smoothing_window)
    
    # Add speaker IDs to output DataFrame
    clustered_df = df.copy()
    clustered_df["speaker_id"] = labels
   

    # 2D projection for plotting
    if use_umap and X_cluster.shape[1] >= 2:
        clustered_df["x"] = X_cluster[:, 0]
        clustered_df["y"] = X_cluster[:, 1]
    else:
        pca_fallback = PCA(n_components=6, random_state=69)
        coords = pca_fallback.fit_transform(X_cluster)
        clustered_df["x"] = coords[:, 0]
        clustered_df["y"] = coords[:, 1]
        print("📉 UMAP disabled — fallback PCA projection used for cluster plot.")

    # Speaker summary
    summary_df = clustered_df.groupby("speaker_id").size().reset_index(name="frame_count")
    
    return clustered_df, summary_df



def smooth_labels_fn(labels, window=5):
    """
    Applies a rolling mode filter to stabilize speaker label assignments.
    """
    smoothed = []
    for i in range(len(labels)):
        start = max(0, i - window)
        end = min(len(labels), i + window + 1)
        segment = labels[start:end]
        mode = scipy.stats.mode(segment, keepdims=False).mode
        smoothed.append(mode)
    return np.array(smoothed)


def apply_umap(X, params=None, verbose=True):
    """
    Applies UMAP dimensionality reduction to a feature matrix.

    Parameters:
        X (np.ndarray): Input feature matrix (scaled)
        params (dict): UMAP parameters
        verbose (bool): Whether to print shape info

    Returns:
        np.ndarray: UMAP-reduced feature matrix
    """
    import umap

    params = params or {}
    reducer = umap.UMAP(
        n_neighbors=params.get("n_neighbors", 10),
        min_dist=params.get("min_dist", 0.3),
        n_components=params.get("n_components", 6),
        metric=params.get("metric", "cosine"),
        n_epochs=params.get("n_epochs", 100),
        low_memory=False,
        random_state=params.get("random_state", 69)
    )

    X_reduced = reducer.fit_transform(X)

    
    if verbose:
        print(f"📉 UMAP applied → shape: {X_reduced.shape}")
    return X_reduced

def assign_speakers_to_segments(clustered_df, segments):
    """
    Assigns a dominant speaker ID to each Whisper segment using majority vote 
    from clustered frame-level speaker labels.
    
    Parameters:
        clustered_df (pd.DataFrame): Must contain 'time' and 'speaker_id' columns.
        segments (List[Dict]): List of Whisper segments (with 'start', 'end', 'id').

    Returns:
        List[Dict]: Segments with added 'speaker' label.
    """
    labeled_segments = []
    
    for segment in segments:
        start, end = segment["start"], segment["end"]
        
        # Select clustered frames within segment boundaries
        mask = (clustered_df["time"] >= start) & (clustered_df["time"] <= end)
        matched_speakers = clustered_df.loc[mask, "speaker_id"]
        
        # Assign most frequent speaker label
        assigned_speaker = int(matched_speakers.mode()[0]) if not matched_speakers.empty else -1

        segment_with_speaker = segment.copy()
        segment_with_speaker["speaker"] = assigned_speaker
        labeled_segments.append(segment_with_speaker)

    return labeled_segments


# ────────────────────────────────────────────────
# Diarization Pipeline Helper Methods
# ────────────────────────────────────────────────

def tag_frames_with_segments(frames_df, segments, frame_time_col="time"):
    """
    Tags each frame with both:
    - the merged `new_segment_id` (post-merge)
    - the original Whisper `segment_id` (pre-merge)

    Drops frames that do not fall within any segment window.
    """
    import pandas as pd

    #pd.DataFrame(frames_df).to_csv(r"C:\demo\interview\tag_segments_frames_input.csv", index=False)

    new_segment_ids = []
    original_segment_ids = []

    for frame_time in frames_df[frame_time_col]:
        match = next(
            (seg for seg in segments if seg["start"] <= frame_time < seg["end"]),
            None
        )
        if match:
            new_segment_ids.append(match.get("new_segment_id"))
            original_segment_ids.append(match.get("id"))
        else:
            new_segment_ids.append(None)
            original_segment_ids.append(None)

    df_out = frames_df.copy()
    df_out["new_segment_id"] = new_segment_ids
    df_out["segment_id"] = original_segment_ids

    df_out = df_out[df_out["new_segment_id"].notna()].copy()
    pd.DataFrame(df_out).to_csv(r"C:\demo\tag_segments_output.csv", index=False)

    return df_out
