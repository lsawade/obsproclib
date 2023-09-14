"""

This will not be executed as part of the pytest suite, but can be invoked by

.. code:: bash

    mpirun -np 4 python test_process_mpi.py

"""

import os
import obspy
import obsproclib as oprc

SCRIPT = os.path.abspath(__file__)
SCRIPTDIR = os.path.dirname(__file__)
DATADIR = os.path.join(SCRIPTDIR, "testdatabase")
CMTFILE = os.path.join(DATADIR, "C200811240902A")
WAVEFORMS = os.path.join(DATADIR, "data", "synthetic.mseed")
STATIONS = os.path.join(DATADIR, "stations.xml")
PROCESSFILE = os.path.join(DATADIR, "process.toml")


def test_queue_multiprocessing():

    # Event data
    latitude = 54.2700
    longitude = 154.7100
    origin_time = obspy.UTCDateTime(2008, 11, 24,  9,  2, 58.80)

    # Loading and fixing the processin dictionary
    processdict = oprc.read_toml(PROCESSFILE)
    processdict["inventory"] = obspy.read_inventory(STATIONS)
    processdict["starttime"] = origin_time \
        + processdict["relative_starttime"]
    processdict["endtime"] = origin_time \
        + processdict["relative_endtime"]
    processdict.pop("relative_starttime")
    processdict.pop("relative_endtime")
    processdict.update(dict(
        remove_response_flag=True,
        event_latitude=latitude,
        event_longitude=longitude,
        geodata=True)
    )

    # Load waveforms
    stream = obspy.read(WAVEFORMS)

    # Reset
    processed_stream_q = oprc.queue_multiprocess_stream(
        stream, processdict, nproc=4, verbose=True)
    print("queue")
    print(processed_stream_q.select(network="G", station="TAOE"))


if __name__ == "__main__":
    test_queue_multiprocessing()
