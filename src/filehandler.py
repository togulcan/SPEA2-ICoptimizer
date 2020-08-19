import os
import threading
from shutil import copytree, copy2
from contextlib import suppress, contextmanager

_local = threading.local()


@contextmanager
def acquire(*locks):
    locks = sorted(locks, key=lambda x: id(x))

    acquired = getattr(_local, 'acquired', [])
    if acquired and max(id(lock) for lock in acquired) >= id(locks[0]):
        raise RuntimeError('Lock Order Violation')

    # Acquire all of the locks
    acquired.extend(locks)
    _local.acquired = acquired
    try:
        for lock in locks:
            lock.acquire()
        yield
    finally:
        # Release locks in reverse order of acquisition
        for lock in reversed(locks):
            lock.release()
        del acquired[-len(locks):]


class FileHandler:

    def __init__(self, path: str):
        self.path = path
        self.multithread = 1

    def check_required_files(self, multithread):
        """
        The circuit folders will be pasted and copied in order for
        one thread to lookup only one folder. The folders will
        be in <circuitname>_temp folder.

        Args:
            multithread (int): number of threads to be used

        """

        if multithread is not None:
            if not isinstance(multithread, int):
                raise TypeError(f"Number of multi thread should be an integer")
            if not 9 > multithread > 0:
                raise ValueError(f"Number of threads must be in range 1-8 but"
                                 f"{multithread} was given.")

        self.multithread = multithread
        source = self.path
        source_temp = source[:-1] + '_temp\\'
        dests = [source_temp + str(i) for i in range(8)]

        assert os.path.isdir(source), \
            f"There is no direction as {source}. " \
            f"In order for simulator to work properly " \
            f"please form the folder first then create the " \
            f"necessary files such as .sp, .geo files. " \
            f"Your files should be in /{self.path}/<circuitname> folder where " \
            f"circuitname was assigned in configs.yaml file."

        with suppress(FileExistsError):
            os.makedirs(source_temp)
        for dest in dests:
            with suppress(FileExistsError):
                os.makedirs(dest)

        for dest in dests:
            self._copy_tree(source, dest)

    @staticmethod
    def _copy_tree(source, destination):
        for item in os.listdir(source):
            s = os.path.join(source, item)
            d = os.path.join(destination, item)
            if os.path.isdir(s):
                copytree(s, d)
            else:
                if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                    copy2(s, d)

    def get_simulation_folder(self):
        if self.multithread > 1:
            return self.path[:-1] + '_temp\\'
        return self.path
