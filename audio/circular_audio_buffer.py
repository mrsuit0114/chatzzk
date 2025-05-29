import threading


class CircularAudioBuffer:
    def __init__(self, capacity_bytes: int):
        self.buffer = bytearray(capacity_bytes)
        self.capacity = capacity_bytes
        self.write_pos = 0
        self.lock = threading.Lock()

    def write(self, data: bytes):
        data_len = len(data)
        if data_len >= self.capacity:
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

    def get_all_data(self):
        with self.lock:
            return bytes(self.buffer[self.write_pos :] + self.buffer[: self.write_pos])
