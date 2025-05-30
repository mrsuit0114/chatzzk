import threading


class CircularAudioBuffer:
    """Thread-safe circular buffer for storing audio data in bytes."""

    def __init__(self, capacity_bytes: int):
        self.buffer = bytearray(capacity_bytes)
        self.capacity = capacity_bytes
        self.write_pos = 0
        self.lock = threading.Lock()
        self.total_written_bytes = 0
        self.total_written_bytes_lock = threading.Lock()

    def write(self, data: bytes):
        """
        Write bytes data into the circular buffer.

        If data length exceeds buffer capacity, only the last capacity bytes are stored.

        Args:
            data (bytes): Audio data bytes to write into buffer.
        """
        data_len = len(data)
        with self.total_written_bytes_lock:
            self.total_written_bytes += data_len

        if data_len >= self.capacity:
            with self.lock:
                self.buffer[:] = data[-self.capacity :]
                self.write_pos = 0
            self.is_full = True
            return

        end_pos = self.write_pos + data_len

        if end_pos <= self.capacity:
            # 버퍼 끝까지 여유 공간 있을 때
            with self.lock:
                self.buffer[self.write_pos : end_pos] = data
                self.write_pos = end_pos % self.capacity
        else:
            with self.lock:
                # 버퍼 끝과 처음을 넘나들며 저장
                first_part = self.capacity - self.write_pos
                second_part = data_len - first_part
                self.buffer[self.write_pos :] = data[:first_part]
                self.buffer[:second_part] = data[first_part:]
                self.write_pos = second_part

    def get_and_reset_written_bytes(self) -> int:
        """
        Get the total number of bytes written since last reset and reset the counter.

        Returns:
            int: Total number of bytes written since last reset.
        """
        with self.total_written_bytes_lock:
            written = self.total_written_bytes
            self.total_written_bytes = 0
            return written

    def get_all_data(self) -> bytes:
        """
        Retrieve all data from the buffer in chronological order, starting from the oldest data.

        Returns:
            bytes: Concatenated bytes of the buffered audio data.
        """
        with self.lock:
            return bytes(self.buffer[self.write_pos :] + self.buffer[: self.write_pos])
