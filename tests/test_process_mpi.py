"""

This will not be executed as part of the pytest suite, but can be invoked by

.. code:: bash

    mpirun -np 4 python test_process_mpi.py

"""

import os
from pprint import pprint
import obspy
import obsproclib as oprc


try:
    from mpi4py import MPI
    mpimode = True
except ImportError as e:
    print(e)
    mpimode = False

SCRIPT = os.path.abspath(__file__)
SCRIPTDIR = os.path.dirname(__file__)
DATADIR = os.path.join(SCRIPTDIR, "testdatabase")
CMTFILE = os.path.join(DATADIR, "C200811240902A")
WAVEFORMS = os.path.join(DATADIR, "data", "synthetic.mseed")
STATIONS = os.path.join(DATADIR, "stations.xml")
PROCESSFILE = os.path.join(DATADIR, "process.toml")


def manual_test_mpiprocessing():

    if mpimode:

        rank = MPI.COMM_WORLD.Get_rank()

        if rank == 0:

            print("MPI MODE")
            print(f"RANK: {rank}")

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
                remove_response_flag=False,
                event_latitude=latitude,
                event_longitude=longitude,
                geodata=False)
            )

            # Load waveforms
            stream = obspy.read(WAVEFORMS)

        else:
            stream = None
            processdict = None

        processed_stream = oprc.mpi_process_stream(stream, processdict)

        # Can be written
        if rank == 0:
            processed_stream.write(
                "processed_synthetic.mseed", format="MSEED")

    else:
        print("NOT MPI MODE")
        return


if __name__ == "__main__":

    manual_test_mpiprocessing()
