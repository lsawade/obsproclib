

import obspy
from .utils import split_stream_inv
from .process import process_stream

def mpi_process_stream(st: obspy.Stream | None, process_dict: dict | None,
                       verbose: bool = False):
    """MPI wrapper for processing a stream.

    Parameters
    ----------
    st : obspy.Stream
        Stream to be processed.
    process_dict : dict
        Processing dictionary.
    verbose : bool
        verbosity flag

    Returns
    -------
    obspy.Stream
        Processed stream.

    """

    try:
        from mpi4py import MPI
    except ImportError as e:
        print(e)
        raise ImportError("MPI4PY not installed. Please install it to use MPI.")

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if verbose and rank == 0:
        print("-> Splitting stream.")

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


    if verbose and rank == 0:
        print("-> Scattering the streams")

    # Scatter stream chunks
    streamlist = comm.scatter(streamlist, root=0)

    if verbose and rank == 0:
        print("-> Broadcasting the process dictionary")

    # Broadcast process dictionary
    processdict = comm.bcast(processdict, root=0)

    if verbose:
        print(
            f"-> R/S: {rank}/{size} -- "
            f"St: {len(streamlist)} -- "
            f"Inv: {len(processdict['inventory'].get_contents()['channels'])}",
            flush=True)

    # Process
    result = process_stream(streamlist, **processdict)

    if verbose:
        print(f"-> Rank: {rank}/{size} -- Done.", flush=True)

    # Make Gatherable result list
    results = []
    results.append(result)

    if verbose and rank == 0:
            print("-> Gathering results")

    results = comm.gather(results, root=0)

    # Sort
    if rank == 0:

        if verbose:
            print("-> Summing stream")

        # Flatten list of lists.
        resultst = obspy.Stream()

        for _result in results:
            resultst += _result[0]

        processed_stream = resultst

        return processed_stream

    else:

        return None
