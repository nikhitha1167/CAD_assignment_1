# CAD_assignment_1
Design of a logic simulator which can simulate a digital circuit which can take input as gate level netlist (verilog), and give output as logical value.

IMPLEMENTATION STEPS

Create the Required Files
First, create the following files in the same folder:

logic_simulator.py

fulladder.v

input_vectors.txt

The file logic_simulator.py contains the Python logic simulator.
The file fulladder.v contains the structural Verilog description of the full adder.
The file input_vectors.txt contains the input combinations to be simulated.

Open the terminal in the folder containing the files.
Run the following command:
python logic_simulator.py fulladder.v input_vectors.txt output_results.txt

After simulation, the calculated results are written into:
output_results.txt
This file contains the simulation results corresponding to the input vector
