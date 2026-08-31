import re
import sys
import os
from collections import defaultdict


# ============================================================
# SUPPORTED LOGIC GATES
# ============================================================

SUPPORTED_GATES = {
    "and",
    "or",
    "nand",
    "nor",
    "xor",
    "xnor",
    "not",
    "buf"
}


# ============================================================
# GATE CLASS
# ============================================================

class Gate:

    def __init__(self, gate_type, name, output_signal, input_signals):

        self.gate_type = gate_type.upper()
        self.name = name
        self.output_signal = output_signal
        self.input_signals = input_signals

        self.level = 0
        self.value = None

    # --------------------------------------------------------
    # Evaluate one gate
    # --------------------------------------------------------

    def evaluate(self, signal_values):

        inputs = []

        for signal in self.input_signals:

            if signal not in signal_values:

                raise ValueError(
                    f"Value of signal '{signal}' "
                    f"is not available for gate {self.name}"
                )

            inputs.append(signal_values[signal])

        # -----------------------------
        # AND
        # -----------------------------

        if self.gate_type == "AND":

            self.value = int(all(inputs))

        # -----------------------------
        # OR
        # -----------------------------

        elif self.gate_type == "OR":

            self.value = int(any(inputs))

        # -----------------------------
        # NAND
        # -----------------------------

        elif self.gate_type == "NAND":

            self.value = int(not all(inputs))

        # -----------------------------
        # NOR
        # -----------------------------

        elif self.gate_type == "NOR":

            self.value = int(not any(inputs))

        # -----------------------------
        # XOR
        # -----------------------------

        elif self.gate_type == "XOR":

            self.value = int(sum(inputs) % 2)

        # -----------------------------
        # XNOR
        # -----------------------------

        elif self.gate_type == "XNOR":

            self.value = int(sum(inputs) % 2 == 0)

        # -----------------------------
        # NOT
        # -----------------------------

        elif self.gate_type == "NOT":

            self.value = int(not inputs[0])

        # -----------------------------
        # BUFFER
        # -----------------------------

        elif self.gate_type == "BUF":

            self.value = inputs[0]

        else:

            raise ValueError(
                f"Unsupported gate type: {self.gate_type}"
            )

        # Store gate output

        signal_values[self.output_signal] = self.value

        return self.value


# ============================================================
# REMOVE VERILOG COMMENTS
# ============================================================

def remove_comments(content):

    # Remove // comments

    content = re.sub(
        r"//.*",
        "",
        content
    )

    # Remove /* ... */ comments

    content = re.sub(
        r"/\*.*?\*/",
        "",
        content,
        flags=re.DOTALL
    )

    return content


# ============================================================
# CLEAN SIGNAL NAME
# ============================================================

def clean_signal(signal):

    signal = signal.strip()

    # Remove bus range

    signal = re.sub(
        r"\[[^\]]+\]",
        "",
        signal
    )

    signal = signal.strip()

    # Remove punctuation

    signal = signal.rstrip(",;")

    return signal


# ============================================================
# PARSE INPUT / OUTPUT DECLARATIONS
# ============================================================

def parse_declarations(content, keyword):

    signals = []

    # --------------------------------------------------------
    # Traditional Verilog style
    #
    # input wire a, b, cin;
    # output wire sum, carry;
    # --------------------------------------------------------

    pattern = re.compile(
        rf"\b{keyword}\b\s+"
        r"(?:wire\s+|reg\s+)?"
        r"([^;]+);",
        re.IGNORECASE
    )

    for match in pattern.finditer(content):

        block = match.group(1)

        for item in block.split(","):

            item = item.strip()

            item = re.sub(
                r"\[[^\]]+\]",
                "",
                item
            )

            item = item.strip()

            match_signal = re.match(
                r"^([A-Za-z_]\w*)$",
                item
            )

            if match_signal:

                name = match_signal.group(1)

                if name not in signals:

                    signals.append(name)

    # --------------------------------------------------------
    # ANSI-style Verilog
    #
    # input wire a,
    # input wire b,
    # input wire cin,
    #
    # output wire sum,
    # output wire carry
    # --------------------------------------------------------

    ansi_pattern = re.compile(
        rf"\b{keyword}\b\s+"
        r"(?:wire\s+|reg\s+)?"
        r"([A-Za-z_]\w*)"
        r"\s*(?:,|\))",
        re.IGNORECASE
    )

    for match in ansi_pattern.finditer(content):

        name = match.group(1)

        if name not in signals:

            signals.append(name)

    return signals


# ============================================================
# PARSE VERILOG NETLIST
# ============================================================

def parse_verilog_netlist(filename):

    with open(filename, "r") as f:

        content = f.read()

    # Remove comments

    content = remove_comments(content)

    # --------------------------------------------------------
    # Find primary inputs
    # --------------------------------------------------------

    primary_inputs = parse_declarations(
        content,
        "input"
    )

    # --------------------------------------------------------
    # Find primary outputs
    # --------------------------------------------------------

    primary_outputs = parse_declarations(
        content,
        "output"
    )

    # --------------------------------------------------------
    # Find gates
    # --------------------------------------------------------

    gates = []

    gate_pattern = re.compile(

        r"\b"
        r"(and|or|nand|nor|xor|xnor|not|buf)"
        r"\s+"
        r"([A-Za-z_]\w*)"
        r"\s*"
        r"\((.*?)\)"
        r"\s*;",
        
        re.IGNORECASE | re.DOTALL
    )

    for match in gate_pattern.finditer(content):

        gate_type = match.group(1).lower()

        gate_name = match.group(2)

        port_block = match.group(3)

        # Split signals

        signals = [

            clean_signal(x)

            for x in port_block.split(",")

        ]

        signals = [

            x for x in signals

            if x
        ]

        if len(signals) < 2:

            continue

        # In Verilog primitive gates:
        #
        # nand g1 (output, input1, input2);
        #
        # First signal = output
        # Remaining signals = inputs

        output_signal = signals[0]

        input_signals = signals[1:]

        gate = Gate(

            gate_type,
            gate_name,
            output_signal,
            input_signals
        )

        gates.append(gate)

    if not gates:

        raise ValueError(
            "No supported gate instances "
            "were found in the Verilog file."
        )

    return (
        primary_inputs,
        primary_outputs,
        gates
    )


# ============================================================
# BUILD DEPENDENCY GRAPH
# ============================================================

def build_graph(gates):

    # Which gate produces each signal?

    driver = {}

    for gate in gates:

        if gate.output_signal in driver:

            raise ValueError(
                f"Multiple gates drive signal "
                f"'{gate.output_signal}'."
            )

        driver[gate.output_signal] = gate

    # dependencies[gate]
    #
    # stores gates which must be executed
    # before this gate

    dependencies = {

        gate: set()

        for gate in gates
    }

    # dependents[gate]
    #
    # stores gates which depend on this gate

    dependents = {

        gate: set()

        for gate in gates
    }

    # --------------------------------------------------------
    # Find dependencies
    # --------------------------------------------------------

    for gate in gates:

        for signal in gate.input_signals:

            if signal in driver:

                previous_gate = driver[signal]

                dependencies[gate].add(
                    previous_gate
                )

                dependents[previous_gate].add(
                    gate
                )

    return (
        driver,
        dependencies,
        dependents
    )


# ============================================================
# LEVELIZE GATES
# ============================================================

def levelize_gates(
    gates,
    dependencies,
    dependents
):

    # Number of dependencies for every gate

    indegree = {

        gate: len(dependencies[gate])

        for gate in gates
    }

    # Preserve original Verilog order

    order_index = {

        gate: index

        for index, gate in enumerate(gates)
    }

    # Gates with no previous gate dependency

    queue = [

        gate

        for gate in gates

        if indegree[gate] == 0
    ]

    queue.sort(
        key=lambda gate: order_index[gate]
    )

    levelized_gates = []

    # --------------------------------------------------------
    # Topological sorting
    # --------------------------------------------------------

    while queue:

        gate = queue.pop(0)

        levelized_gates.append(gate)

        # If no previous gate,
        # it is Level 1

        if not dependencies[gate]:

            gate.level = 1

        else:

            gate.level = (

                max(
                    previous.level
                    for previous in dependencies[gate]
                )

                + 1
            )

        # Find next gates

        ready_gates = []

        for next_gate in dependents[gate]:

            indegree[next_gate] -= 1

            if indegree[next_gate] == 0:

                ready_gates.append(
                    next_gate
                )

        ready_gates.sort(
            key=lambda gate: order_index[gate]
        )

        queue.extend(
            ready_gates
        )

    # --------------------------------------------------------
    # Check for combinational loop
    # --------------------------------------------------------

    if len(levelized_gates) != len(gates):

        raise ValueError(
            "Combinational feedback loop detected. "
            "The netlist cannot be levelized."
        )

    return levelized_gates


# ============================================================
# DISPLAY GATE INFORMATION
# ============================================================

def display_gate_information(gates):

    print("\n")
    print("=" * 70)

    print(
        "GATE INFORMATION"
    )

    print("=" * 70)

    for gate in gates:

        print(

            f"{gate.name:<5}"
            f": {gate.gate_type:<5}"
            f" Output = {gate.output_signal:<7}"
            f" Inputs = {', '.join(gate.input_signals)}"

        )


# ============================================================
# DISPLAY LEVELIZATION
# ============================================================

def display_levelization(
    levelized_gates
):

    levels = defaultdict(list)

    for gate in levelized_gates:

        levels[gate.level].append(
            gate.name
        )

    print("\n")
    print("=" * 70)

    print(
        "GATE LEVELIZATION"
    )

    print("=" * 70)

    for level in sorted(levels):

        print(

            f"Level {level}: "
            +
            ", ".join(
                levels[level]
            )

        )

    print("=" * 70)


# ============================================================
# SIMULATE ONE INPUT VECTOR
# ============================================================

def simulate_vector(

    vector,

    primary_inputs,

    primary_outputs,

    levelized_gates

):

    vector = vector.strip()

    # --------------------------------------------------------
    # Check number of bits
    # --------------------------------------------------------

    if len(vector) != len(primary_inputs):

        raise ValueError(

            f"Input vector '{vector}' has "
            f"{len(vector)} bits, but the circuit has "
            f"{len(primary_inputs)} primary inputs."
        )

    # --------------------------------------------------------
    # Check only 0 and 1
    # --------------------------------------------------------

    if any(

        bit not in "01"

        for bit in vector

    ):

        raise ValueError(

            f"Input vector '{vector}' "
            "must contain only 0 and 1."
        )

    # Dictionary containing signal values

    signal_values = {}

    # --------------------------------------------------------
    # Assign primary input values
    # --------------------------------------------------------

    for signal, bit in zip(

        primary_inputs,
        vector

    ):

        signal_values[signal] = int(bit)

    # --------------------------------------------------------
    # Evaluate gates according to levels
    # --------------------------------------------------------

    for gate in levelized_gates:

        gate.evaluate(
            signal_values
        )

    # --------------------------------------------------------
    # Check outputs
    # --------------------------------------------------------

    for output in primary_outputs:

        if output not in signal_values:

            raise ValueError(

                f"Value of primary output "
                f"'{output}' could not be calculated."
            )

    # --------------------------------------------------------
    # Generate output vector
    # --------------------------------------------------------

    output_vector = ""

    for output in primary_outputs:

        output_vector += str(
            signal_values[output]
        )

    return output_vector


# ============================================================
# READ INPUT VECTOR FILE
# ============================================================

def read_vectors(input_vector_file):

    vectors = []

    with open(
        input_vector_file,
        "r"
    ) as f:

        for line in f:

            line = line.strip()

            # Ignore blank lines

            if not line:

                continue

            # Ignore comments

            if line.startswith("#"):

                continue

            if line.startswith("//"):

                continue

            # Remove spaces
            #
            # Example:
            # 0 0 1
            #
            # becomes:
            # 001

            line = re.sub(
                r"\s+",
                "",
                line
            )

            vectors.append(
                line
            )

    if not vectors:

        raise ValueError(

            f"No input vectors found in "
            f"'{input_vector_file}'."
        )

    return vectors


# ============================================================
# SIMULATE INPUT VECTOR FILE
# ============================================================

def simulate_from_vector_file(

    input_vector_file,

    output_file,

    primary_inputs,

    primary_outputs,

    levelized_gates

):

    vectors = read_vectors(
        input_vector_file
    )

    results = []

    # --------------------------------------------------------
    # Simulate every vector
    # --------------------------------------------------------

    for vector in vectors:

        output = simulate_vector(

            vector,

            primary_inputs,

            primary_outputs,

            levelized_gates

        )

        result = (

            vector
            +
            " --> "
            +
            output

        )

        results.append(
            result
        )

    # --------------------------------------------------------
    # Write results to output file
    # --------------------------------------------------------

    with open(
        output_file,
        "w"
    ) as f:

        for result in results:

            f.write(
                result + "\n"
            )

    return results


# ============================================================
# PRINT USAGE
# ============================================================

def print_usage():

    print("\n")
    print("Usage:")
    print()
    print(
        "Single vector:"
    )

    print(
        "python logic_simulator.py "
        "fulladder.v 101"
    )

    print()
    print(
        "Multiple vectors from file:"
    )

    print(
        "python logic_simulator.py "
        "fulladder.v "
        "input_vectors.txt "
        "output_results.txt"
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    # --------------------------------------------------------
    # Check command line arguments
    # --------------------------------------------------------

    if len(sys.argv) < 3:

        print_usage()

        sys.exit(1)

    if len(sys.argv) > 4:

        print_usage()

        sys.exit(1)

    # --------------------------------------------------------
    # Get Verilog file
    # --------------------------------------------------------

    verilog_file = sys.argv[1]

    if not os.path.isfile(
        verilog_file
    ):

        print(
            f"\nERROR: Verilog file "
            f"'{verilog_file}' not found."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Parse Verilog
    # --------------------------------------------------------

    try:

        (
            primary_inputs,
            primary_outputs,
            gates

        ) = parse_verilog_netlist(
            verilog_file
        )

        (
            driver,
            dependencies,
            dependents

        ) = build_graph(
            gates
        )

        levelized_gates = levelize_gates(

            gates,

            dependencies,

            dependents

        )

    except Exception as error:

        print(
            f"\nERROR: {error}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Display circuit information
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)

    print(
        "LOGIC SIMULATOR"
    )

    print("=" * 70)

    print(
        "Primary Inputs : "
        +
        ", ".join(
            primary_inputs
        )
    )

    print(
        "Primary Outputs: "
        +
        ", ".join(
            primary_outputs
        )
    )

    print(
        "Number of Gates: "
        +
        str(
            len(gates)
        )
    )

    # --------------------------------------------------------
    # Display gates
    # --------------------------------------------------------

    display_gate_information(
        levelized_gates
    )

    # --------------------------------------------------------
    # Display levelization
    # --------------------------------------------------------

    display_levelization(
        levelized_gates
    )

    # ========================================================
    # MODE 1
    #
    # Single input vector
    #
    # Example:
    #
    # python logic_simulator.py fulladder.v 101
    # ========================================================

    if len(sys.argv) == 3:

        vector = sys.argv[2]

        try:

            output = simulate_vector(

                vector,

                primary_inputs,

                primary_outputs,

                levelized_gates

            )

            print("\n")
            print("=" * 70)

            print(
                "SIMULATION RESULT"
            )

            print("=" * 70)

            print(
                f"{vector} --> {output}"
            )

            print("=" * 70)

        except Exception as error:

            print(
                f"\nERROR: {error}"
            )

            sys.exit(1)

    # ========================================================
    # MODE 2
    #
    # Input vector file + output file
    #
    # Example:
    #
    # python logic_simulator.py fulladder.v
    # input_vectors.txt output_results.txt
    # ========================================================

    else:

        input_vector_file = sys.argv[2]

        output_file = sys.argv[3]

        # ----------------------------------------------------
        # Check input vector file
        # ----------------------------------------------------

        if not os.path.isfile(
            input_vector_file
        ):

            print(

                f"\nERROR: Input vector file "
                f"'{input_vector_file}' not found."

            )

            sys.exit(1)

        # ----------------------------------------------------
        # Simulate all vectors
        # ----------------------------------------------------

        try:

            results = simulate_from_vector_file(

                input_vector_file,

                output_file,

                primary_inputs,

                primary_outputs,

                levelized_gates

            )

            # ------------------------------------------------
            # Display results
            # ------------------------------------------------

            print("\n")
            print("=" * 70)

            print(
                "SIMULATION RESULTS"
            )

            print("=" * 70)

            for result in results:

                print(result)

            print("=" * 70)

            print()

            print(
                "Results successfully saved to:"
            )

            print(
                output_file
            )

        except Exception as error:

            print(
                f"\nERROR: {error}"
            )

            sys.exit(1)


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()