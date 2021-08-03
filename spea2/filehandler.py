import os
import threading
from contextlib import contextmanager, suppress
from shutil import copy2, copytree, rmtree

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

    def form_simulation_environment(self, multithread):
        """
        The circuit folders will be pasted and copied in order for
        one thread to lookup only one folder. The folders will
        be in <circuitname>_temp folder.

        Args:
            multithread (int): number of threads to be used

        """
        self.multithread = multithread

        if multithread == 1: return

        source = self.path
        source_temp = source[:-1] + '_temp/'
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

    def delete_simulation_environment(self):
        """ The folders where simulations executed will be deleted. """
        if self.multithread == 1: return

        path = self.get_folder_path()
        try:
            rmtree(path)
        except OSError as e:
            print("Error ", path, ":", e.strerror)

    def get_folder_path(self):
        """
        Returns:
            path to the temporary simulation folder.
        """
        if self.multithread > 1:
            return self.path[:-1] + '_temp\\'
        return self.path
