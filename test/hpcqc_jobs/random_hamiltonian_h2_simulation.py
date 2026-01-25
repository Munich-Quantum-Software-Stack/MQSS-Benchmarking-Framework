import os
import math
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt

from qiskit_aer import AerSimulator

from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister
from qiskit.quantum_info.operators import Operator

from time import process_time, sleep, perf_counter
from datetime import datetime, timezone
from scipy.optimize import minimize

from mqss.qiskit_adapter import MQSSQiskitAdapter

# ------------------------------------------
# For Logging
# ------------------------------------------
logger = logging.getLogger("random_hamiltonian_h2_simulation")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s")
# logging.basicConfig(filename='hpcqc_vqe_random_hamiltonian_h2.log', level=logging.INFO)

global NUMTH_EXE_ITER

# ------------------------------------------
# Util Functions
# ------------------------------------------
int2bit     = lambda x, n: str(bin(x)[2:].zfill(n))
bit2int     = lambda b: int("".join(str(bs) for bs in b), base=2)
bit2pauli   = lambda x: x.replace("0", "I").replace("1", "Z")

def gen_hamiltonian_base():
    """Return the precomputed hamiltonian of the H2 molecule
    at the bond length of 0.

    Args: None

    Returns:
        List of coefficients and pauli terms, along with the offsets
    """
    H = [
        ("ZIII", 0.17110545123720233),
        ("IZII", 0.17110545123720225),
        ("ZZII", 0.16859349595532533),
        ("YXXY", 0.04533062254573469),
        ("YYXX", -0.04533062254573469),
        ("XXYY", -0.04533062254573469),
        ("XYYX", 0.04533062254573469),
        ("IIZI", -0.22250914236600539),
        ("ZIZI", 0.12051027989546245),
        ("IIIZ", -0.22250914236600539),
        ("ZIIZ", 0.16584090244119712),
        ("IZIZ", 0.16584090244119712),
        ("IIZZ", 0.12051027989546245),
        ("ZZZZ", 0.1743207725924201),
    ]
    return H, -0.09963387941370971

def generate_random_diagonal_hamiltonian(n):
    np.random.seed(seed=42)
    N = 2**n
    values = np.random.rand(N, 1) * 5
    H = [(bit2pauli(int2bit(idx, n)), val) for idx, val in enumerate(values)]
    return H

def gen_hamiltonian(bases, N, offset=0):
    """Convert the decomposed Hamiltonian terms into a full
    matrix representation for proof testing.

    Args:
        bases (list): List of Pauli terms and their coefficients.

    Returns:
        np.array: Hamiltonian matrix.
    """

    Z = np.array([[1.0, 0j], [0.0, -1.0]])
    Y = np.array([[0, -1j], [1j, 0]])
    X = np.array([[0j, 1], [1, 0]])
    I = np.eye(2)

    operator_dict = {"I": I, "X": X, "Y": Y, "Z": Z}

    # return a 2-D array with ones on the diagonal and zeros elsewhere
    # this case is offset + 0j
    H = np.eye(2**N) * offset + 0j

    # construct the Hamiltonian matrix term by term
    for terms in bases:
        ops, coeff = terms
        matrix = coeff
        for op in ops:
            # computes the Kronecker product, a composite array made of blocks
            # of the second array scaled by the first
            matrix = np.kron(matrix, operator_dict[op])
        H += matrix

    return H

def convert_counts_to_expval(counts, total_shots, basis=None):
    """Given the counts as measurement type, find the expectation value for the given term in the hamiltonian

    Args:
        counts (dict): Counts of measurement results.
        total_shots (int): Total number of measurement shots.
        basis (str): Measurement basis for each qubit.

    Returns:
        float: Computed expectation value.
    """
    expectation = 0.0
    if basis == None:
        basis = [("Z", 1)]
    for bit_string, count in counts.items():
        weighted_count = count
        for i, bit in enumerate(bit_string[::-1]):
            if basis[i] != "I":
                # Qubit is measured
                # Apply sign flip if qubit is in state |1>
                if bit == "1":
                    weighted_count *= -1
        expectation += weighted_count
    expectation /= total_shots
    return expectation

def run_circuit(params, num_qubits, backend, num_shots, basis=None, draw_flag=False):
    """Run a quantum circuit based on the provided parameters and measurement basis.

    Args:
        params (list): Parameters for the Rx and Ry rotations.
        basis (str): Measurement basis for each qubit.
        draw_flag (bool): If True, prints the circuit.

    Returns:
        float: Expectation value from the measurement results.
    """

    q = QuantumRegister(num_qubits)
    c = ClassicalRegister(num_qubits)
    circuit = QuantumCircuit(q, c)
    N = num_qubits

    # initial state (Hartree-Fock state)
    # a unique parameterized rgate running on each individual qubit
    for i in range(N):
        circuit.r(*(params[2 * i : (2 * (i + 1))]), i)

    for i in range(N):
        circuit.cx(i, (i + 1) % N)
    circuit.barrier()

    for i in range(N):
        circuit.r(*(params[2 * N + (2 * i) : (2 * N) + (2 * (i + 1))]), i)
    for i in range(N):
        circuit.measure(q[i], c[i])

    local_start_run_time = datetime.now()
    start_run_time = perf_counter()
    # assume some delay here between submission and execution start
    job = backend.run(circuit, shots=num_shots)
    local_complete_run_time = datetime.now()
    end_run_time = perf_counter()
    result = job.result()
    NUMTH_EXE_ITER += 1
    print('------------------------------------------')
    print(f"-------- Iteration {NUMTH_EXE_ITER} ---------")
    print(f"Local start run timestamp: {local_start_run_time}")
    print(f"Local complete run timestamp: {local_complete_run_time}")

    # profile time the execution
    profiled_execution = (start_run_time, end_run_time)

    # post-processing the results
    counts = result.get_counts()
    exp_val = convert_counts_to_expval(counts, num_shots, basis)
    if draw_flag == True:
        circuit.draw(output="mpl")

    return exp_val, profiled_execution

def objective_func(params, num_qubits, backend, num_shots, bases, offset, profiled_qpu_time_arr):
    """Optimization function to minimize.

    Args:
        params (list): Parameters for the quantum circuit.

    Returns:
        float: Computed energy expectation value.
    """

    # involved variables
    global idx

    # offset for the Hamiltonian (coefficient that corresponds to Identity)
    exp_val = offset

    # sum the contributions of all terms in the Hamiltonian
    print(f"Opt. iteration {idx}: running with params {params}")
    for terms in bases:
        ops, coeffs = terms
        try:
            cir_output, profiled_data = run_circuit(params, num_qubits, backend, num_shots, ops)
            exp_val += cir_output * coeffs
            profiled_qpu_time_arr.append(profiled_data)
        except TypeError as error:
            raise error
        completion_time = profiled_data[1] - profiled_data[0] # in seconds
        print(f"\tTerms: {terms}, complete_time={completion_time}s")
        print(f"\tEnergy: {exp_val}")
    exp_vals.append(exp_val)

    # increase the iter counter
    idx += 1

    return exp_val

def find_opt_params(num_qubits, backend, num_shots, maxiters, bases, offset, profiled_qpu_data):
    """Perform the optimization to find the best parameters.

    Returns:
        Result of the optimization process.
    """
    np.random.seed(seed=42)
    N = num_qubits
    params = np.random.rand(N * N) * np.pi
    options = {'maxiter': maxiters}

    opt_res = minimize(
        objective_func,
        params,
        method="COBYLA",
        args=(num_qubits, backend, num_shots, bases, offset, profiled_qpu_data),
        options=options
    )
    return opt_res

def visualize_convergence(exp_vals, ground_truth):
    # figure configuration
    plt.figure(figsize=(8, 5))

    # plot the list of exp_vals as a dashed line
    plt.plot(exp_vals, linestyle="--", color="blue", marker="x", label="Expectation Values")

    # store handles for unique legend entries
    handles = [
        plt.Line2D([], [], color="blue", linestyle="--", marker="x", label="Expectation Values")
    ]

    if type(ground_truth) == list or type(ground_truth) == np.ndarray:
        orange_added = False
        red_added = False
        for i in range(len(ground_truth)):
            color = "orange"
            if i == np.argmin(ground_truth):
                color = "red"
            plt.axhline(y=ground_truth[i], color=color, linestyle="-", label="Eigenvalues of H")

            # Add legend handles for red and orange lines only once
            if color == "orange" and not orange_added:
                handles.append(
                    plt.Line2D([], [], color="orange", linestyle="-", label="Eigenvalues of H")
                )
                orange_added = True
            if color == "red" and not red_added:
                handles.append(
                    plt.Line2D([], [], color="red", linestyle="-", label="Minimum Eigenvalue")
                )
                red_added = True
    else:
        # plot the ground truth as a solid line
        plt.axhline(y=ground_truth, color="red", linestyle="-", label="Ground Truth")

    # adding labels and title
    plt.xlabel("Iteration")
    plt.ylabel("Value")
    plt.title("Ground state energy")
    plt.legend(handles=handles)
    plt.grid(True)

    # show the plot or save to file
    save_path = "./vqe_random_hamiltonian_results.pdf"
    plt.savefig(save_path, bbox_inches="tight")
    # plt.show()

# ------------------------------------------
# Main Function
# ------------------------------------------
if __name__ == "__main__":

    # argument declaration
    parser = argparse.ArgumentParser()
    parser.add_argument("-bak", "--backend", type=str, default="AerSimulator", 
                        help="Type of the backend we want to run")
    parser.add_argument("-qub", "--qubits", type=int, default=4, 
                        help="The amount of numbers/qubits we want to randomly generate")
    parser.add_argument("-sho", "--shots", type=int, default=1000, 
                        help="The numbers of shots we want to run the circuit with")
    parser.add_argument("-max", "--maxiter", type=int, default=100, 
                        help="The maximum number of iterations for optimization")
    args = vars(parser.parse_args())

    backend_name = args["backend"]
    if backend_name == "AerSimulator":
        backend = AerSimulator()
    else:
        token_val = "hskHPJhuLBkh2WvhNemZRjUBpySy4LoeWW3Gjh8HFsgxtAega9zxwU8b4Bn4NMCC"
        mqss_adapter = MQSSQiskitAdapter(token=token_val)
        [backend] = mqss_adapter.backends(name=backend_name)
    
    num_qubits = args["qubits"]
    num_shots  = args["shots"]
    max_iters  = args["maxiter"]
    N = num_qubits
    NUMTH_EXE_ITER = 0

    # generate hamiltonian
    bases = generate_random_diagonal_hamiltonian(N)
    offset = 0
    H = gen_hamiltonian(bases, N, offset)

    print('------------------------------------------')
    print('Generated random diagonal Hamiltonian for %d qubits.', N)
    print('Hamiltonian matrix: shape=%s', H.shape)
    print('VQE Opt. max iters: %d', max_iters)
    print('------------------------------------------')

    # calculate the ground state (result) by classical linear algorithm
    ev, eg = np.linalg.eig(H)
    ground_truth = np.min(ev).real

    print('------------------------------------------')
    print('Using np.linalg to calculate eigen values and vectors')
    print('Ground state energy: %.6f', ground_truth)
    print('------------------------------------------')

    # calculate and find the result by VQE
    exp_vals = []
    profiled_qpu_time_arr = []
    idx = 0

    start_time = process_time()
    opt_res = find_opt_params(num_qubits, backend, num_shots, max_iters, bases, offset, profiled_qpu_time_arr)
    stop_time = process_time()

    print('------------------------------------------')
    print('Converged energy: %.6f', opt_res.fun)
    print('Elapsed time: %.6fs', (stop_time-start_time))
    print('------------------------------------------')

    # visualize the comparison between ground_truth and opt. exp. results
    visualize_convergence(exp_vals, ground_truth)
    # visualize_convergence(exp_vals, ev)

