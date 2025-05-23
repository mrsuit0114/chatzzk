class CircularAudioBuffer:
    def __init__(self, capacity_bytes: int):
        self.buffer = bytearray(capacity_bytes)
        self.capacity = capacity_bytes
        self.write_pos = 0
        self.is_full = False

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
            self.buffer[self.write_pos : end_pos] = data
            self.write_pos = end_pos % self.capacity
        else:
            # 버퍼 끝과 처음을 넘나들며 저장
            first_part = self.capacity - self.write_pos
            self.buffer[self.write_pos :] = data[:first_part]
            second_part = data_len - first_part
            self.buffer[:second_part] = data[first_part:]
            self.write_pos = second_part

        if not self.is_full and self.write_pos == 0:
            self.is_full = True

    def get_all_data(self):
        if not self.is_full:
            # 아직 버퍼를 다 채우지 않은 상태
            return bytes(self.buffer[: self.write_pos])
        else:
            # 버퍼가 가득 차서 write_pos부터 끝까지 + 처음부터 write_pos까지 순서로 읽기
            return bytes(self.buffer[self.write_pos :] + self.buffer[: self.write_pos])
