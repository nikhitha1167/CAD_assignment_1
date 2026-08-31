# CAD_assignment_1
Design of a logic simulator which can simulate a digital circuit which can take input as gate level netlist (verilog), and give output as logical value.

How to Run the Program

 1. Keep these files in the same folder: logic_simulator.py, fulladder.v, input_vectors.txt and output_results.txt (the output file may be created automatically).
   
   The file logic_simulator.py contains the Python logic simulator.

   The file fulladder.v contains the structural Verilog description of the full adder.

   The file input_vectors.txt contains the input combinations to be simulated.

 2. Open Command Prompt or PowerShell in that folder.
   
 3. Check Python installation using:
    
    python --version
   
 5. Run the complete batch simulation using:
    
    python logic_simulator.py fulladder.v input_vectors.txt output_results.txt
   
 7. The program displays the primary inputs, primary outputs, number of gates, gate information and gate levelization.
 
 8. It then simulates all vectors in input_vectors.txt
 
 9. The final results are saved in output_results.txt
