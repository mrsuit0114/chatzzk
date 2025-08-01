# models.py
import json
from dataclasses import dataclass


@dataclass
class ChannelMonitorStatus:
    channel_id: str
    deployment_name: str

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        return cls(**json.loads(json_str))
