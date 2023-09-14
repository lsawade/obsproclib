from datetime import datetime
import multiprocessing
from typing import Callable, Iterable, Optional, List
import queue


def get_results(
        processes: List[multiprocessing.Process],
        resultQueue: multiprocessing.Queue):

    results = []
    while True:
        try:
            result = resultQueue.get(False, 0.01)
            results.append(result)
        except queue.Empty:
            pass
        allExited = True
        for t in processes:
            if t.exitcode is None:
                allExited = False
                break
        if allExited & resultQueue.empty():
            break

    return results


def process_wrapper(queue, _i, processfunc, verbose, *args, **kwargs):
    if verbose:
        print(f"START: Process {_i} -- {datetime.now()} -- {processfunc.__name__}()")

    queue.put((_i, processfunc(*args, **kwargs)))

    if verbose:
        print(f"STOP:  Process {_i} -- {datetime.now()}")


def multiwrapper(
        proc: Callable,
        args: Iterable = tuple(),
        kwargs: Iterable = tuple(),
        verbose: bool = False):
    """Wraps a simple Queue/Process setup to  execute a function in parallel.

    Parameters
    ----------
    proc : Callable
        Processing function
    args : Iterable
        arguments, iterable of tuple
    kwargs : Iterable
        keyword arguments, iterable of dictionaries
    verbose : bool
        whether to print info flags

    Returns
    -------
    Iterable
        List of sorted results

    Notes
    -----

    :Author:
        Lucas Sawade (lsawade@princeton.edu)

    :Last Modified:
        2021.06.11 14.15

    """

    # You need a queue to store the output from each worker
    q: multiprocessing.Queue = multiprocessing.Queue()

    # Creating the processing queue
    if verbose:
        print("Adding jobs to the queue")
    jobs = []
    for _i, (_arg, _kwargs) in enumerate(zip(args, kwargs)):

        # For each _arg, _kwargs pair, we will start one process
        pro = multiprocessing.Process(
            target=process_wrapper,
            # The following line is fairly important
            # next to the arguments we also have to provide the queue,
            # the index of the input arguments, and the callable to be
            # executed on the processor AND the args ...
            args=(q, _i, proc, verbose, *_arg),
            # .. and kwargs. So, the
            kwargs=_kwargs)

        # Then start the process and append it to the list.
        pro.start()
        jobs.append(pro)

    if verbose:
        print("Finished adding jobs to queue")

    # The statement below works well if you are not getting anything from
    # the queue. That is if you maybe only process files in parallel.
    # It does however often hang when dealing with getting things form the
    # queue. Therefore, I now use the get_results function, which checks whether
    # everything is done and whether the result queue is empty instead.
    # I'm only leaving this because it is good to know. And simpler if
    # One is only processing in parallel without needing the results.
    #
    # Then, we join the processes (sort of a wait for everything to be done
    # statement)
    # for _i, pro in enumerate(jobs):
    #     print(f"Print before joining {_i}")
    #     pro.join()

    # if verbose:
    #     print("Finished joining")

    # Then, the results are gathered. This function is rather important.
    results = get_results(jobs, q)

    if verbose:
        print("Finished getting results")

    # This is where the job index becomes important. Since the processes may
    # start and finish at different times depending on the arg and kwarg sets,
    # the output will be putt into the queue at different times. We use i to
    # sort the output.
    sorted_by_first = sorted(results, key=lambda tup: tup[0])

    # Only get the results of the function
    final_results = [t[1] for t in sorted_by_first]

    return final_results
