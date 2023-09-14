import typing as tp
import obspy
try:
    import tomllib
except ImportError:
    import toml as tomllib
import time


def read_toml(filename: str) -> dict:
    return tomllib.load(filename)


def sec2hhmmss(seconds: float, roundsecs: bool = True) \
        -> tp.Tuple[int, int, tp.Union[float, int]]:
    """Turns seconds into tuple of (hours, minutes, seconds)

    Parameters
    ----------
    seconds : float
        seconds

    Returns
    -------
    Tuple
        (hours, minutes, seconds)

    Notes
    -----
    :Author:
        Lucas Sawade (lsawade@princeton.edu)

    :Last Modified:
        2021.03.05 18.44

    """

    # Get hours
    hh = int(seconds // 3600)

    # Get minutes
    mm = int((seconds - hh * 3600) // 60)

    # Get seconds
    ss = (seconds - hh * 3600 - mm * 60)

    if roundsecs:
        ss = round(ss)

    return (hh, mm, ss)


def sec2timestamp(seconds: float) -> str:
    """Gets time stamp from seconds in format "hh h mm m ss s"

    Parameters
    ----------
    seconds : float
        Seconds to get string from

    Returns
    -------
    str
        output timestamp
    """

    hh, mm, ss = sec2hhmmss(seconds)
    return f"{int(hh):02} h {int(mm):02} m {int(ss):02} s"


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer:
    timers: tp.ClassVar[tp.Dict[str, float]] = dict()
    name: tp.Optional[str] = None
    text: str = "     Elapsed time: {:s} seconds"
    logger: tp.Optional[tp.Callable[[str], None]] = print
    _start_time = None

    def __init__(self, plogger=print):
        self.logger = plogger

    def __post_init__(self) -> None:
        """Add timer to dict of timers after initialization"""
        if self.name is not None:
            self.timers.setdefault(self.name, 0)

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        # Calculate elapsed time
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None

        # Report elapsed time
        if self.logger:
            self.logger(self.text.format(sec2timestamp(elapsed_time)))
        if self.name:
            self.timers[self.name] += elapsed_time

        return elapsed_time

    def __enter__(self):
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Stop the context manager timer"""
        self.stop()


def split(container, count):
    """
    Simple function splitting a container into equal length chunks.
    Order is not preserved but this is potentially an advantage depending on
    the use case.
    """
    return [container[_i::count] for _i in range(count)]


def split_stream_inv(
    obsd: obspy.Stream,
    inv: obspy.Inventory,
    synt: tp.Optional[obspy.Stream] = None,
    nprocs=4) -> \
        tp.Tuple[
        tp.List[obspy.Stream],
        tp.List[obspy.Inventory]] | \
        tp.Tuple[
        tp.List[obspy.Stream],
        tp.List[obspy.Stream],
        tp.List[obspy.Inventory]]:
    """Split stream and inventory into chunks for parallel processing. The
    optional synthetic stream is good for windowing. Splits synthetics and
    observations into stationwise chunks. Station-wise because we want to rotate
    the traces usually.

    Parameters
    ----------
    obsd : obspy.Stream
        input stream
    inv : obspy.Inventory
        input inventory
    synt : obspy.Stream, optional
        input synthetic stream, by default None
    nprocs : int, optional
        number of processes, by default 4


    Returns
    -------
    tuple of (obspy.Stream, obspy.Inventory) or
        tuple of (obspy.Stream, obspy.Stream, obspy.Inventory)
        Processed stream(s) and inventory

    """

    # Split up stations into station chunks
    stations = [x.split()[0] for x in inv.get_contents()['stations']]
    sstations = split(stations, nprocs)

    # Split up traces into chunks containing full stations
    sobsd, sinv = [], []
    if synt is not None:
        ssynt = []

    # Loop over stationlists
    for _stalist in sstations:

        # Create substreams and inventories
        subinv = obspy.Inventory()
        obsd_substream = obspy.Stream()

        if synt is not None:
            synt_substream = obspy.Stream()

        # Loop over stations within list
        for _sta in _stalist:

            network, station = _sta.split(".")

            # Select Network and Stations
            subinv += inv.select(network=network, station=station)
            obsd_substream += obsd.select(network=network, station=station)

            # Select synt if given
            if synt is not None:
                synt_substream += synt.select(network=network, station=station)

        # Append to chunked lists
        sinv.append(subinv)
        sobsd.append(obsd_substream)

        if synt is not None:
            ssynt.append(synt_substream)

    # Return depending on input.
    if synt is not None:
        return sobsd, ssynt, sinv
    else:
        return sobsd, sinv


def stream_multiply(st: obspy.Stream, factor: float):
    """Acts on stream and multiplies included data by a `factor`

    Parameters
    ----------
    st : Stream
        stream to be processed
    factor : float
        factor to multiply traces with

    Last modified: Lucas Sawade, 2020.10.30 14.00 (lsawade@princeton.edu)
    """

    # Loop over traces
    for tr in st:
        tr.data *= factor
