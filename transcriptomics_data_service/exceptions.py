__all__ = [
    "TakuanException",
    "TakuanDBException",
]


class TakuanException(Exception):
    pass


class TakuanDBException(TakuanException):
    pass
