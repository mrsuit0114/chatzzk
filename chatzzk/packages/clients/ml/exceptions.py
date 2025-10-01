"""
Custom exceptions for ML clients.
"""


class MLException(Exception):
    """Base exception for all ML client errors."""

    pass


class ASRError(MLException):
    """Raised for errors during ASR processing."""

    pass


class VADError(MLException):
    """Raised for errors during VAD processing."""

    pass
