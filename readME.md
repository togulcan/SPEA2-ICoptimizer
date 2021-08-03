Multi-Objective IC Optimizer with SPEA2 Evolutionary Algorithm
==============================================================

*Author*: **Tuğberk Oğulcan ÇAKICI** (togulcancakici@gmail.com)   
*Project Supervisors*: **Prof. Günhan Dündar** and **Dr. Engin Afacan**
  
Introduction
============

This is a high level, multi-threaded and pure-python implementation of SPEA2 (Strength Pareto Evolutionary Algorithm) 
on IC (Integrated Circuit) optimization where circuits with best performance are obtained despite the 
trade-off among the objectives.

Multi-objective optimization (MOO) algorithms are frequently deployed
 in circuit optimization and evolutionary
algorithms are especially popular due to nonlinearity of the
problem. They thoroughly scan the design space
and choose the non-dominated solutions to reach a final Pareto
optimal front (POF).

### Background

Many analog circuit sizing tools can be found in literature. 
The most common type is optimization-based tools.
The main process of circuit optimization is as follows. The
designer chooses a circuit topology and defines the design
space, which includes the design parameters of passive components 
(transistor widths and lengths, bias currents
and voltages, resistor, capacitor, and inductor values). The
designer can also provide some constraints to the circuit
such as maximum power and area. In most cases, a Pareto
optimal front (POF) is preferred over a single optimized
circuit since the aim is to obtain a set of possible solutions
spread over the design space. POFs are obtained when more
than one objectives are optimized and show the trade-off
between various objectives.

How To Use
==========

First, navigate into the project folder and create a virtual 
environment (Python3.7 or greater required) then activate it. 
After, install dependencies with the following command:

````
$ pip install -r requirements.txt
````

If you will use HSpice as high level simulator install it and 
make sure it can be successfully called from terminal. You can see how 
the program calls the command in ``src.simulators.HSpiceSimulator`` class. 
If, however, you want to use another simulator you need to implement it by inheriting from `BaseSimulator`.

Circuit files that are used to simulate should be in ``circuitfiles/<circuit_name>/`` and
specified in ``configs.yaml`` file. Before launching the process make sure your circuit 
filesare all correct and simulation results are being written to the same directory without any
failure. Since the algorithm initializes the first generation until all circuits are simulated
correctly if the circuit files are defected the process will be stuck in infinite loop.

### Usage Example

````
$ python -m spea2 --only_cct --config_path=configs.yaml --saving_mode=numpy --thread=8
````

### Arguments

- only_cct: saves only circuit data and discards fitness data
- config_path: path to configs.yaml
- saving_mode: if equals 'instance' the data will be saved as instance of Generation. 
if equals 'numpy' the data will be appended to a numpy.ndarray
- thread: number of threads to be used. 

It is recommended to set saving_mode to 'numpy' when the number of generations and the
number of individuals are excessively high where memory footprint is a critical concern.


### Configurations
An example for Single Stage Amplifier(SSA) is as follows:

````yaml
Circuit:
  name: amp
  type: analog
  transistor_number: 6 #How many transistors the circuit has
  path_to_circuit: circuitfiles/amp/ #where your circuit files located
  path_to_output: data/amp/ #the data will be pickled here
  technology_L: 130.0e-9 #technology for the circuit
  topology: #these are the varying input parameters of the circuit
    - LM1
    - LM2
    - LM3
    - WM1
    - WM2
    - WM3
    - Ib
  upper_bound: #max values for input parameters
    - 130.0e-8
    - 130.0e-8
    - 130.0e-8
    - 975.0e-7
    - 975.0e-7
    - 975.0e-7
    - 1.0e-3
  lower_bound: #min values for input parameters
    - 130.0e-9
    - 130.0e-9
    - 130.0e-9
    - 650.0e-9
    - 650.0e-9
    - 650.0e-9
    - 10.0e-6
  output: #calculated response of the circuit
    - gain
    - bw
    - himg
    - hreal
    - zsarea
````

where outputs are the response of the simulator and should be specified in ``.sp`` file. 
The algorithm search the individuals whose parameters should be in between upper and lower bound.


An example of settings for the evolutionary algorithm can be:
````yaml
SPEA2:
  maximum_generation: 300 #where to stop iteration
  N: 100 #number of individual per generation
  targets:
    gain: max #this parameter will be maximized
    bw: max #this parameter will be maximized
  constraints:
    pm:
      min: 45 #phase-margin should be at least 45
    zsarea:
      max: 5.0e-9 #area should be lower than 5e-9
````

again these specifications (gain, bw, pm, zsarea etc.) should be defined in your ``.sp`` file or else
``AtrributeError`` exception will be raised during the process.

In the above example, gain and bandwidth of the Single Stage Amplifier are the objectives and should be maximized.

### Example

After the process, the POF of the last generation of SSA example above should look like:

![Example of SSA](https://github.com/togulcan/SPEA2-ICoptimizer/blob/master/docs/pof.png)

In the case of 3 dimensional optimization you just need to add an extra objective 
to config file:
````yaml
targets:
  gain: max
  bw: max
  zpower: min
````
the algorithm tries to maximize 1/zpower instead of minimizing zpower and the result
is as follow:

![Example2 of SSA](https://github.com/togulcan/SPEA2-ICoptimizer/blob/master/docs/pof3d.png)

Conclusion
==========

- An efficient multi-objective IC optimizer using SPEA2 algorithm 
has been proposed and its results has been showed. Due to flexibility of the code any type of 
circuit and simulator can be implemented easily.

- The algorithm can be used only when there is a trade-off between objectives, otherwise the optimization
would be meaningless.

References
==========
1. E. Zitzler, M. Laumanns, and L. Thiele, “SPEA2: Improving the
strength pareto evolutionary algorithm,” *TIK-report*, vol. 103, 2001.

2.  P. Czyzzak and A. Jaszkiewicz, “Pareto simulated annealing- a meta
heuristic technique for multiple-objective combinatorial optimization,” 
*Journal of Multi-Criteria Decision Analysis*, vol. 7, pp. 34–47, 1998.

3. R. Phelps and et. al., “ANACONDA: simulation-based synthesis of
analog circuits via stochastic pattern search,” *IEEE Transactions on
Computer-Aided Design of Integrated Circuits and Systems*, vol. 19,
no. 6, pp. 703–717, June 2000.

4. G. Berkol and et. al., “A novel yield aware multi-objective analog
circuit optimization tool,” in *2015 IEEE International Symposium on
Circuits and Systems (ISCAS)*. IEEE, 2015, pp. 2652–2655.
