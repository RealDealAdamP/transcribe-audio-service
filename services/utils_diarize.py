# File: transcribe_audio_service/services/utils_diarize.py

import librosa 
import torch
from silero_vad import load_silero_vad, get_speech_timestamps
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
import hdbscan
import numpy as np
import scipy.stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import torch


def run_diarization_pipeline(audio_path, whisper_segments, return_summary_only=False, diagnostics=True):
    diagnostics_snapshots = {}


    # Step 0: Load audio + apply VAD
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    is_voiced = get_vad_voiced_mask(y, sr=sr, hop_length=160)

    
    # Step 1: Extract Librosa features (frame-level)
    identify_audio_df = run_librosa_identification(y, sr=sr, is_voiced=is_voiced)
    print(identify_audio_df.head(35))
    # Step 2: Smooth + scale
    identify_audio_df = smooth_audio_features(
        identify_audio_df, window=3, method="median", scale=True, scale_type="zscore"
    )
    print(len(identify_audio_df.index))
	
	#Step 2.5 Apply PCA 
    frame_pca_df = apply_groupwise_pca(identify_audio_df)
    
	
    #print(frame_pca_df.columns)
    # Step 3: Frame-level clustering using full features (no aggregation)
    clustered_df, speaker_summary = cluster_full_features(frame_pca_df)
    #clustered_df, speaker_summary = cluster_kmeans_auto(frame_pca_df, max_k=50)
    # Step 4: (To be added) Map frame-level speaker labels back to Whisper segments

    if diagnostics:
        diagnostics_snapshots["frame_level_clustering"] = speaker_summary

    result = {
        "speaker_frames": clustered_df,  # frame-level output
        "speaker_summary": speaker_summary
    }

    if diagnostics:
        result["diagnostics"] = diagnostics_snapshots

    return result




# ────────────────────────────────────────────────
# Diarization Pipeline Helper Methods
# ────────────────────────────────────────────────

def get_vad_voiced_mask(
    y,
    sr=16000,
    hop_length=160,
    threshold=0.5,
    min_speech_duration_ms=250,
    max_speech_duration_s=15
):
    """
    Run Silero VAD and return a frame-level mask indicating voiced frames.

    Parameters:
        y (np.ndarray): Audio waveform.
        sr (int): Sample rate (default 16000).
        hop_length (int): Frame hop size.
        threshold (float): VAD probability threshold.
        min_speech_duration_ms (int): Minimum speech segment duration.
        max_speech_duration_s (float): Maximum speech segment duration to merge.

    Returns:
        frame_voiced (np.ndarray): Boolean array [n_frames] aligned with Librosa frame times.
    """
    try:
        model = load_silero_vad()
        print("✅ Silero VAD model loaded (direct import)")
    except Exception as e:
        import traceback
        print("❌ ERROR: Failed to load Silero VAD model")
        traceback.print_exc()
        raise e

    # 📦 Run VAD
    audio_tensor = torch.FloatTensor(y)
    speech_timestamps = get_speech_timestamps(
        audio_tensor,
        model,
        sampling_rate=sr,
        threshold=threshold,
        min_speech_duration_ms=min_speech_duration_ms,
        max_speech_duration_s=max_speech_duration_s,
        return_seconds=True  # ⏱️ this gives start/end in seconds
    )

    # 🕒 Frame-to-time conversion for voiced mask
    n_frames = int(np.ceil(len(y) / hop_length))
    frame_times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop_length)
    frame_voiced = np.zeros(n_frames, dtype=bool)

    for ts in speech_timestamps:
        start_sec = ts['start']
        end_sec = ts['end']
        frame_voiced |= (frame_times >= start_sec) & (frame_times <= end_sec)

    # 📊 Debug summary
    voiced_count = np.sum(frame_voiced)
    print(f"🗣️ VAD marked {voiced_count} / {n_frames} frames as voiced ({voiced_count / n_frames:.1%})")

    return frame_voiced

def run_librosa_identification(y, sr=16000, hop_length=160, is_voiced=None):
    import numpy as np
    import librosa
    import pandas as pd
    import time

    timings = {}

    n_fft = 512
    n_mfcc = 13
    n_mels = 40
    fmax = 4000

    # ⏱️ MFCCs
    t0 = time.time()
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels, fmax=fmax)
    mfcc = librosa.feature.mfcc(S=librosa.power_to_db(mel_spec), n_mfcc=n_mfcc)
    timings["mfcc"] = time.time() - t0

    # Other features
    delta_mfcc = librosa.feature.delta(mfcc)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft)
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft)
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft)
    spectral_flatness = librosa.feature.spectral_flatness(y=y, hop_length=hop_length, n_fft=n_fft)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft)
    rms = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length)
    zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=n_fft, hop_length=hop_length)
    f0 = librosa.yin(y=y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr, hop_length=hop_length)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length, n_fft=n_fft)

    # 🕒 Frame timing
    n_frames = mfcc.shape[1]
    frame_times = librosa.frames_to_time(np.arange(n_frames), sr=sr, hop_length=hop_length)

    # ⛑️ Ensure VAD mask matches frame count
    if is_voiced is not None and len(is_voiced) > n_frames:
        is_voiced = is_voiced[:n_frames]

    # 📦 Construct feature DataFrame
    df = pd.DataFrame({
        "time": frame_times,
        **{f"mfcc_{i+1}": mfcc[i] for i in range(n_mfcc)},
        **{f"delta_mfcc_{i+1}": delta_mfcc[i] for i in range(n_mfcc)},
        "spectral_centroid": spectral_centroid[0][:n_frames],
        "spectral_bandwidth": spectral_bandwidth[0][:n_frames],
        "spectral_flatness": spectral_flatness[0][:n_frames],
        "spectral_rolloff": spectral_rolloff[0][:n_frames],
        "rms": rms[0][:n_frames],
        "zcr": zcr[0][:n_frames],
        "pitch": f0[:n_frames],
        **{f"spectral_contrast_{i+1}": spectral_contrast[i][:n_frames] for i in range(spectral_contrast.shape[0])},
        **{f"chroma_{i+1}": chroma[i][:n_frames] for i in range(chroma.shape[0])}
    })

    # 🧹 Apply VAD filter (drop non-voiced frames)
    if is_voiced is not None:
        df["is_voiced"] = is_voiced
        df = df[df["is_voiced"] == 1].reset_index(drop=True)

    return df





def smooth_audio_features(
    df,
    window=3,
    method="mean",           # "mean" or "median"
    scale=True,
    scale_type="zscore",     # or "minmax"
    smoothing_cols=None,
    exclude_columns=["time", "tempo"]
):
    """
    Smooth and optionally scale features in a frame-level Librosa DataFrame.

    Parameters:
        df (pd.DataFrame): Input frame-level feature DataFrame.
        window (int): Rolling window size for smoothing.
        method (str): 'mean' or 'median' smoothing.
        scale (bool): Whether to apply feature scaling.
        scale_type (str): 'zscore' or 'minmax'.
        smoothing_cols (list): Explicit columns to smooth. Default = all numeric features except exclude_columns.
        exclude_columns (list): Columns to exclude from smoothing and scaling.

    Returns:
        pd.DataFrame: Smoothed and optionally scaled feature DataFrame.
    """
    smoothed_df = df.copy()

    # Default: all numeric features except excluded
    if smoothing_cols is None:
        smoothing_cols = [
            col for col in df.columns
            if col not in exclude_columns and df[col].dtype in [float, int]
        ]

    # Apply smoothing
    if method == "mean":
        smoothed = df[smoothing_cols].rolling(window=window, center=True, min_periods=1).mean()
    elif method == "median":
        smoothed = df[smoothing_cols].rolling(window=window, center=True, min_periods=1).median()
    else:
        raise ValueError("Invalid smoothing method. Use 'mean' or 'median'.")

    smoothed_df[smoothing_cols] = smoothed

    # Apply scaling if requested
    if scale:
        scaler = StandardScaler() if scale_type == "zscore" else MinMaxScaler()
        smoothed_df[smoothing_cols] = scaler.fit_transform(smoothed_df[smoothing_cols])

    return smoothed_df



def apply_groupwise_pca(
    df,
    n_components=1,
    whiten=False,
    svd_solver='auto',
    random_state=69
):
    """
    Applies PCA separately to each logical group of frame-level features.
    Returns a DataFrame with 1 or more PCA components per group (plus time).

    Parameters:
        df (pd.DataFrame): Input DataFrame with frame-level features and a 'time' column.
        n_components (int or float): Number of PCA components to retain per group.
        whiten (bool): Whether to apply whitening.
        svd_solver (str): PCA solver to use ('auto', 'full', 'randomized', etc.).
        random_state (int): Seed for reproducibility.
    """
    output = pd.DataFrame()
    output["time"] = df["time"].values  # Preserve frame alignment

    feature_groups = {
        "mfcc":       [col for col in df.columns if col.startswith("mfcc_")],
        "delta_mfcc": [col for col in df.columns if col.startswith("delta_mfcc_")],
        "contrast":   [col for col in df.columns if col.startswith("spectral_contrast_")],
        "energy":     ["rms"],
        "voicing":    ["zcr", "pitch"],
        "timbre":     ["spectral_centroid", "spectral_bandwidth", "spectral_flatness"],
        "rolloff":    ["spectral_rolloff"],
        "chroma":     [col for col in df.columns if col.startswith("chroma_")]
    }

    for group_name, cols in feature_groups.items():
        if not cols:
            continue

        X = df[cols].fillna(0).values

        # If single-feature group, skip PCA
        if X.shape[1] == 1:
            output[f"{group_name}_pca_1"] = X[:, 0]
        else:
            pca = PCA(
                n_components=n_components,
                whiten=whiten,
                svd_solver=svd_solver,
                random_state=random_state
            )
            reduced = pca.fit_transform(X)

            for i in range(reduced.shape[1]):
                output[f"{group_name}_pca_{i+1}"] = reduced[:, i]

    print(f"🧬 Groupwise PCA complete → {len(output.columns) - 1} components added.")
    print(output.index)
    return output


def cluster_full_features(
    df,
    min_cluster_size=None,
    min_samples=None,
    confidence_threshold=0.3,
    smooth_labels=True,
    smoothing_window=3
):
    """
    Performs HDBSCAN clustering using the full feature set on frame-level data.

    Parameters:
        df (pd.DataFrame): Frame-level Librosa features (smoothed + scaled)
        min_cluster_size (int): Minimum cluster size for HDBSCAN (default: scaled)
        min_samples (int): Minimum samples for core points (default: scaled)
        confidence_threshold (float): Points below this are labeled -1 (noise)
        smooth_labels (bool): Whether to smooth speaker IDs using a rolling mode
        smoothing_window (int): Window size for smoothing (e.g., 3 = ±3)

    Returns:
        clustered_df (pd.DataFrame): Frame-level DataFrame with 'speaker_id'
        summary_df (pd.DataFrame): Summary of frame counts per speaker_id
    """
    # 🧪 Prepare feature matrix
    exclude = ["time"]
    feature_cols = [col for col in df.columns if col not in exclude and df[col].dtype in [float, int]]
    feature_matrix = df[feature_cols].fillna(0).values
    X_scaled = StandardScaler().fit_transform(feature_matrix)

    # 📐 Dynamic clustering parameters
    n_frames = len(df)
    if min_cluster_size is None:
        min_cluster_size = max(10, int(0.005 * n_frames))
    if min_samples is None:
        min_samples = max(2, int(0.001 * n_frames))

    print(f"🧪 Clustering {n_frames} frames → min_cluster_size={min_cluster_size}, min_samples={min_samples}")

    # 🔗 Fit HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples
    ).fit(X_scaled)

    labels = clusterer.labels_
    probs = clusterer.probabilities_

    # ❗ Reassign low-confidence points to noise
    labels[probs < confidence_threshold] = -1

    # 🔁 Optional: temporal smoothing
    if smooth_labels:
        labels = smooth_labels_fn(labels, window=smoothing_window)

    # 📦 Assemble output
    clustered_df = df.copy()
    clustered_df["speaker_id"] = labels
    summary_df = clustered_df.groupby("speaker_id").size().reset_index(name="frame_count")

    return clustered_df, summary_df


def smooth_labels_fn(labels, window=3):
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

def cluster_kmeans_auto(df, max_k=15, min_k=2, scale=True):
    """
    Performs KMeans clustering with dynamic k selection based on silhouette score.

    Parameters:
        df (pd.DataFrame): Frame-level features (smoothed + scaled)
        max_k (int): Maximum number of clusters to test
        min_k (int): Minimum number of clusters to test
        scale (bool): Whether to standardize features

    Returns:
        clustered_df (pd.DataFrame): Frame-level DataFrame with speaker_id
        summary_df (pd.DataFrame): Speaker frame count summary
    """
    exclude = ["time"]
    feature_cols = [col for col in df.columns if col not in exclude and df[col].dtype in [float, int]]
    X = df[feature_cols].fillna(0).values
    if scale:
        X = StandardScaler().fit_transform(X)

    best_k = None
    best_score = -1
    best_labels = None

    for k in range(min_k, max_k + 1):
        kmeans = KMeans(n_clusters=k, n_init="auto", random_state=42)
        labels = kmeans.fit_predict(X)
        
        try:
            score = silhouette_score(X, labels)
            if score > best_score:
                best_score = score
                best_k = k
                best_labels = labels
        except ValueError:
            continue  # handle rare empty cluster

    print(f"✅ Best k = {best_k} (silhouette score = {best_score:.4f})")

    clustered_df = df.copy()
    clustered_df["speaker_id"] = best_labels

    summary_df = clustered_df.groupby("speaker_id").size().reset_index(name="frame_count")

    return clustered_df, summary_df