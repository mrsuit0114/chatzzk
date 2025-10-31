"""
Custom exceptions for ML clients.
"""


class MlException(Exception):
    """Base exception for all ML client errors."""

    pass


class ASRError(MlException):
    """Raised for errors during ASR processing."""

    pass


class VADError(MlException):
    """Raised for errors during VAD processing."""

    pass
