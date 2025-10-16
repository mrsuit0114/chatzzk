"""
Custom exceptions for ML clients.
"""


class MlException(Exception):
    """Base exception for all ML client errors."""

    pass


class AsrError(MlException):
    """Raised for errors during Asr processing."""

    pass


class VadError(MlException):
    """Raised for errors during Vad processing."""

    pass
