import threading


class CircularAudioBuffer:
    """Thread-safe circular buffer for storing audio data in bytes."""

    def __init__(self, capacity_bytes: int):
        self.buffer = bytearray(capacity_bytes)
        self.capacity = capacity_bytes
        self.write_pos = 0
        self.buffer_lock = threading.Lock()
        self.last_speech_timestamp_idx = 0

    def write(self, data: bytes):
        """
        Write bytes data into the circular buffer.
        If data length exceeds buffer capacity, only the last capacity bytes are stored.
        last_speech_timestamp_idx is decremented by data length because the buffer is circular.

        Args:
            data (bytes): Audio data bytes to write into buffer.
        """
        data_len = len(data)
        with self.buffer_lock:
            self.last_speech_timestamp_idx -= data_len
            self.last_speech_timestamp_idx = max(self.last_speech_timestamp_idx, 0)

            if data_len >= self.capacity:
                self.buffer[:] = data[-self.capacity :]
                self.write_pos = 0
                return

            end_pos = self.write_pos + data_len

            if end_pos <= self.capacity:
                # 버퍼 끝까지 여유 공간 있을 때
                self.buffer[self.write_pos : end_pos] = data
                self.write_pos = end_pos % self.capacity
            else:
                # 버퍼 끝과 처음을 넘나들며 저장
                first_part = self.capacity - self.write_pos
                second_part = data_len - first_part
                self.buffer[self.write_pos :] = data[:first_part]
                self.buffer[:second_part] = data[first_part:]
                self.write_pos = second_part

    def update_last_speech_timestamp_idx(self, idx: int) -> None:
        """Add idx as much as the number of bytes processed.

        Args:
            idx (int): number of bytes processed
        """
        with self.buffer_lock:
            self.last_speech_timestamp_idx += idx

    def get_all_data(self) -> bytes:
        """
        Retrieve all data from the buffer in chronological order, starting from the oldest data.

        Returns:
            bytes: Concatenated bytes of the buffered audio data.
        """
        with self.buffer_lock:
            data = (self.buffer[self.write_pos :] + self.buffer[: self.write_pos])[self.last_speech_timestamp_idx :]
            return data[:-1] if len(data) % 2 == 1 else data
