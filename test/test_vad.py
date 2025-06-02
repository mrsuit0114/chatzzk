# diart, whisperX, faster whisper, silero VAD

import gc
import json
import os
import time
import warnings

import GPUtil
import matplotlib.pyplot as plt
import numpy as np
import psutil
import torch
import torchaudio
import whisperx
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

warnings.filterwarnings("ignore")


def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        "ram": memory_info.rss / 1024 / 1024,  # MB
        "gpu": GPUtil.getGPUs()[0].memoryUsed if torch.cuda.is_available() else 0,  # MB
    }


def load_audio(audio_path):
    """Load audio file and return waveform and sample rate"""
    waveform, sample_rate = torchaudio.load(audio_path)
    return waveform.squeeze().numpy(), sample_rate


def save_results(results, model_name, memory_usage, inference_time):
    """Save VAD results and performance metrics to a JSON file"""
    output_dir = "vad_results"
    os.makedirs(output_dir, exist_ok=True)

    # Convert results to serializable format
    if model_name == "diart":
        serializable_results = [(segment.start, segment.end) for segment in results.itersegments()]
    elif model_name == "whisperx":
        serializable_results = [(segment["start"], segment["end"]) for segment in results["segments"]]
    elif model_name == "faster_whisper":
        serializable_results = [(segment.start, segment.end) for segment in results]
    elif model_name == "silero":
        serializable_results = [(segment["start"] / 16000, segment["end"] / 16000) for segment in results]

    # Save results and performance metrics
    output_data = {
        "performance": {"memory_usage_mb": memory_usage, "inference_time_seconds": inference_time},
        "segments": serializable_results,
    }

    with open(os.path.join(output_dir, f"{model_name}_results.json"), "w") as f:
        json.dump(output_data, f, indent=2)


def run_diart_vad(audio_path):
    """Run VAD using Diart"""
    initial_memory = get_memory_usage()

    pipeline = Pipeline.from_pretrained(
        "pyannote/voice-activity-detection",
        use_auth_token="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",  # HuggingFace token needed
    )
    start_time = time.time()
    vad_results = pipeline(audio_path)

    end_time = time.time()
    final_memory = get_memory_usage()
    memory_usage = {
        "ram": final_memory["ram"] - initial_memory["ram"],
        "gpu": final_memory["gpu"] - initial_memory["gpu"],
    }
    inference_time = end_time - start_time

    save_results(vad_results, "diart", memory_usage, inference_time)
    del pipeline
    gc.collect()
    torch.cuda.empty_cache()
    return vad_results


def run_whisperx_vad(audio_path):
    """Run VAD using WhisperX"""
    initial_memory = get_memory_usage()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisperx.load_model("large-v3", device)
    start_time = time.time()
    result = model.transcribe(audio_path, language="ko")

    end_time = time.time()
    final_memory = get_memory_usage()
    memory_usage = {
        "ram": final_memory["ram"] - initial_memory["ram"],
        "gpu": final_memory["gpu"] - initial_memory["gpu"],
    }
    inference_time = end_time - start_time

    save_results(result, "whisperx", memory_usage, inference_time)
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return result


def run_faster_whisper_vad(audio_path):
    """Run VAD using Faster Whisper"""
    initial_memory = get_memory_usage()

    model = WhisperModel("large-v3", device="cuda" if torch.cuda.is_available() else "cpu")
    start_time = time.time()
    segments, _ = model.transcribe(audio_path, vad_filter=True, language="ko")

    end_time = time.time()
    final_memory = get_memory_usage()
    memory_usage = {
        "ram": final_memory["ram"] - initial_memory["ram"],
        "gpu": final_memory["gpu"] - initial_memory["gpu"],
    }
    inference_time = end_time - start_time

    save_results(segments, "faster_whisper", memory_usage, inference_time)
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return segments


def run_silero_vad(audio_path):
    """Run VAD using Silero VAD"""
    initial_memory = get_memory_usage()

    model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=True)

    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

    wav = read_audio(audio_path, sampling_rate=16000)
    start_time = time.time()
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)

    end_time = time.time()
    final_memory = get_memory_usage()
    memory_usage = {
        "ram": final_memory["ram"] - initial_memory["ram"],
        "gpu": final_memory["gpu"] - initial_memory["gpu"],
    }
    inference_time = end_time - start_time

    save_results(speech_timestamps, "silero", memory_usage, inference_time)
    del model, utils
    gc.collect()
    torch.cuda.empty_cache()
    return speech_timestamps


def load_saved_results():
    """Load saved VAD results from JSON files"""
    results = {}
    output_dir = "vad_results"

    for model_name in ["diart", "whisperx", "faster_whisper", "silero"]:
        file_path = os.path.join(output_dir, f"{model_name}_results.json")
        if os.path.exists(file_path):
            with open(file_path) as f:
                results[model_name] = json.load(f)

    return results


def visualize_vad_results(audio_path, results_dict):
    """Visualize VAD results from different models"""
    waveform, sr = load_audio(audio_path)
    duration = len(waveform) / sr

    plt.figure(figsize=(15, 10))

    # Plot waveform
    plt.subplot(len(results_dict) + 1, 1, 1)
    plt.plot(np.linspace(0, duration, len(waveform)), waveform)
    plt.title("Waveform")
    plt.xlabel("Time (s)")

    # Plot VAD results
    for idx, (model_name, result) in enumerate(results_dict.items(), 2):
        plt.subplot(len(results_dict) + 1, 1, idx)

        for segment in result:
            plt.axvspan(
                segment["start"],
                segment["end"],
                color={"diart": "green", "whisperx": "blue", "faster_whisper": "red", "silero": "purple"}[model_name],
                alpha=0.3,
            )

        plt.title(f"{model_name} VAD Results")
        plt.xlabel("Time (s)")

    plt.tight_layout()
    plt.close()


def print_performance_summary():
    """Print performance summary of all models"""
    output_dir = "vad_results"
    print("\nPerformance Summary:")
    print("-" * 80)
    print(f"{'Model':<15} {'RAM Usage (MB)':<15} {'GPU Usage (MB)':<15} {'Time (s)':<10}")
    print("-" * 80)

    for model_name in ["whisperx", "faster_whisper", "silero"]:
        file_path = os.path.join(output_dir, f"{model_name}_results.json")
        if os.path.exists(file_path):
            with open(file_path) as f:
                data = json.load(f)
                perf = data["performance"]
                print(
                    f"{model_name:<15} {perf['memory_usage_mb']['ram']:<15.2f} "
                    f"{perf['memory_usage_mb']['gpu']:<15.2f} {perf['inference_time_seconds']:<10.2f}"
                )


def main():
    # audio_path = "/workspace/20250419_Dungeon_Fighter_6409220.mp3"  # Replace with your audio file path
    audio_path = "/workspace/20250419_talk_6174188.mp3"  # Replace with your audio file path
    # Run VAD with different models sequentially

    print("Running WhisperX VAD...")
    run_whisperx_vad(audio_path)

    print("Running Faster Whisper VAD...")
    run_faster_whisper_vad(audio_path)

    print("Running Silero VAD...")
    run_silero_vad(audio_path)

    # print("Running Diart VAD...")
    # run_diart_vad(audio_path)

    # Print performance summary
    # print_performance_summary()


if __name__ == "__main__":
    main()
