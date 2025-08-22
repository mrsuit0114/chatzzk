import json


def load_jsonl(file):
    """JSONL 파일 로드"""
    data = []
    for line in file.getvalue().decode("utf-8").strip().split("\n"):
        if line.strip():
            data.append(json.loads(line))
    return data
