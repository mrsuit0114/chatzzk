from urllib.parse import urljoin

import librosa
import m3u8
import numpy as np
import requests

# url = 'https://ex-nlive-streaming.navercdn.com/d980d34705f1661c11f6df39a8476a33/682EBB98/chzzk/lip2_kr/cflexnmss2u0041/b3ukb0vbloimax0anis1siotc1pnzgov7ft6/audioOnly/g6k1xevjjy0rvmd7xti8ohq1pnzgov7c47_chunklist.m3u8'
url = "https://ex-nlive-streaming.navercdn.com/06d3c3278308a92326a5176da2c19e0a/682ECCD6/chzzk/lip2_kr/cflexnmss2u0005/hx5hz0ticpzbrbiuaphmogqbrmf3h6g61iqz/audioOnly/dfrnpih9i11wxgp3xsqamsjmf3h6g61fhq_chunklist.m3u8"
playlist = m3u8.load(url)

# Get base URL for segments
base_url = url.rsplit("/", 1)[0] + "/"

# List to store all audio data
all_audio_data = []


def vad(audio_data):
    pass


def asr(audio_data):
    pass


# Download and process each segment
for i, segment in enumerate(playlist.segments):
    # Combine base URL with segment URL
    segment_url = urljoin(base_url, segment.uri)
    response = requests.get(segment_url)

    if response.status_code == 200:
        # Get the content and ensure it's a multiple of 2 (16-bit = 2 bytes)
        content = response.content
        if len(content) % 2 != 0:
            content = content[:-1]  # Remove last byte if odd length

        # Convert audio data to numpy array
        audio_data = np.frombuffer(content, dtype=np.int16)  # asr에서 float16변환 필요
        all_audio_data.append(audio_data)
        combined_audio = np.concatenate(all_audio_data)
        resampled_audio = librosa.resample(combined_audio, orig_sr=48000, target_sr=16000)

        vad_result = vad(resampled_audio)
        print(f"Processed segment {i}, shape: {audio_data.shape}, content length: {len(content)}")
    else:
        print(f"Failed to download segment {i}")

# Combine all segments
if all_audio_data:
    combined_audio = np.concatenate(all_audio_data)
    print(f"Total audio data shape: {combined_audio.shape}")
