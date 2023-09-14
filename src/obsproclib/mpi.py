

import obspy
from .utils import split_stream_inv
from .process import process_stream
try:
    from mpi4py import MPI
except ImportError as e:
    print(e)
    raise ImportError("MPI4PY not installed. Please install it to use MPI.")


def mpi_process_stream(st: obspy.Stream | None, process_dict: dict | None):
    """MPI wrapper for processing a stream.

    Parameters
    ----------
    st : obspy.Stream
        Stream to be processed.
    process_dict : dict
        Processing dictionary.

    Returns
    -------
    obspy.Stream
        Processed stream.

    """

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        # Check whether stream is None
        if st is None:
            raise ValueError("Stream is None on rank 0.")
        if process_dict is None:
            raise ValueError("Processdict is None on rank 0.")

        # Split the stream into different chunks
        streamlist, _ = split_stream_inv(st, process_dict['inventory'],
                                         nprocs=size)
        processdict = process_dict

    else:

        streamlist = None
        processdict = None

    # Scatter stream chunks
    streamlist = comm.scatter(streamlist, root=0)

    # Broadcast process dictionary
    processdict = comm.bcast(processdict, root=0)

    print(
        f"Stream {len(streamlist)} -- "
        f"Inv: {len(processdict['inventory'].get_contents()['channels'])} -- "
        f"Rank: {rank}/{size}", flush=True)

    # Process
    result = process_stream(streamlist, **processdict)

    # Make Gatherable result list
    results = []
    results.append(result)
    print(f"Rank: {rank}/{size} -- Done.", flush=True)

    results = comm.gather(results, root=0)

    # Sort
    if rank == 0:
        # Flatten list of lists.
        resultst = obspy.Stream()

        for _result in results:
            resultst += _result[0]

        processed_stream = resultst

        return processed_stream

    else:
        return None
