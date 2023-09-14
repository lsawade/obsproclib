from .utils import read_toml, stream_multiply, split_stream_inv
from .process import process_stream
from .queue_multiprocess_stream import queue_multiprocess_stream

__all__ = [
    "read_toml",
    "queue_multiprocess_stream",
    "process_stream",
    "split_stream_inv",
    "stream_multiply",
]

try:
    import mpi4py
    from .mpi import mpi_process_stream
    __all__.append("mpi_process_stream")
except ImportError as e:
    print(e)




