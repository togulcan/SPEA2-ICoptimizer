import os
import yaml
import time
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--only_cct",
                    help="optional argument for saving the fitness data.",
                    action='store_true')
parser.add_argument("--config_path", help="path to configuration .yaml file")
parser.add_argument("--saving_mode", help="this should be either 'numpy' or 'instance'")
parser.add_argument("--thread", help="number of thread to be used'")

args = parser.parse_args()
cfg_path = args.config_path
saving_mode = args.saving_mode
multi_thread = int(args.thread) if args.thread is not None else 1
only_cct = True if args.only_cct else False

# Set logger configurations.
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename='logs.log',
                    format=LOG_FORMAT,
                    level=logging.INFO)
logger = logging.getLogger()

if saving_mode not in ("numpy", "instance"):
    raise RuntimeError(f"Please note that saving_mode argument "
                       f"should be either 'numpy' or 'instance'")

if not 0 < multi_thread < 9:
    raise RuntimeError(f"Number of threads should be in between (1,8) "
                       f"but given {multi_thread}.")

with open(cfg_path) as file:
    yaml_file = yaml.load(file, Loader=yaml.FullLoader)
    CIRCUIT_PROPERTIES = yaml_file["Circuit"]
    SPEA2_PROPERTIES = yaml_file["SPEA2"]

if not os.path.isdir(CIRCUIT_PROPERTIES["path_to_output"]):
    raise SystemExit(f"There is no such direction "
                     f"{CIRCUIT_PROPERTIES['path_to_output']}")

if __name__ == "__main__":
    from src import FileHandler, process

    # Create temp folder to perform simulations
    file_handler = FileHandler(CIRCUIT_PROPERTIES['path_to_circuit'])
    file_handler.form_simulation_environment(multi_thread)
    path = file_handler.get_folder_path()

    # start time_perf counter.
    start = time.perf_counter()

    # start the process
    saved_file_path = process(
        CIRCUIT_PROPERTIES, SPEA2_PROPERTIES, path,
        multi_thread, saving_mode, only_cct
    )

    # stop time_perf counter
    stop = time.perf_counter()

    constraints_as_str = [k + '->' + i + ':' + str(j)
                          for k, v in SPEA2_PROPERTIES['constraints'].items()
                          for i, j in v.items()]
    logger.info(f"\nTime took for the whole process: {(stop - start) / 60} min."
                f"\nMaximum generation: {SPEA2_PROPERTIES['maximum_generation']} "
                f"with {SPEA2_PROPERTIES['N']} individuals for each generation."
                f"\nNumber of threads used: {multi_thread}"
                f"\nSaving Format: {saving_mode}"
                f"\nSaved to {saved_file_path} file."
                f"\nTargets: {', '.join([k + '->' + v for k, v in SPEA2_PROPERTIES['targets'].items()])}"
                f"\nConstraints: {', '.join(constraints_as_str)}"
                f"\nTopology: {CIRCUIT_PROPERTIES['topology']}"
                f"\nUpper bound: {CIRCUIT_PROPERTIES['upper_bound']}"
                f"\nLower bound: {CIRCUIT_PROPERTIES['lower_bound']}\n")

    # Delete the temp folder
    file_handler.delete_simulation_environment()
