#!/bin/sh
#SBATCH -J qaoa_example_timestamp
#SBATCH -o ./%x_%j.out
#SBATCH -e ./%x_%j.err
#SBATCH --ntasks=1
#SBATCH --gres=qpu:1
#SBATCH --cpus-per-task=1
#SBATCH --partition=wolpy
#SBATCH --time=03:00:00

t1_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t1=$(date +%s%3N)
source /home/di35hef/MQSS/MQSS-Benchmarking-Framework/.venv/bin/activate 
t2_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t2=$(date +%s%3N)
echo "[SBATCH] $t1_timestamp: Start loading mqssbench env"
echo "[SBATCH] $t2_timestamp: Finished loading mqssbench env"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to load mqssbench env (ms): $((t2 - t1))"
echo "[SBATCH] -------------------------------------------------"
echo ""

t3_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t3=$(date +%s%3N)
source /home/sw/qis/wolpy/mqss/scripts/load-mqss-qoffload.sh
t4_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t4=$(date +%s%3N)
echo "[SBATCH] $t3_timestamp: Start loading mqss-qoffload env"
echo "[SBATCH] $t4_timestamp: Finished loading mqss-qoffload env"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to load mqss-qoffload env (ms): $((t4 - t3))"
echo "[SBATCH] -------------------------------------------------"
echo ""

# Export the HPCQC flag
export MQSS_TOKEN="hskHPJhuLBkh2WvhNemZRjUBpySy4LoeWW3Gjh8HFsgxtAega9zxwU8b4Bn4NMCC"
export MQSS_URL="https://portal.quantum.lrz.de"
export MQSS_PORT="4000"
export MQSS_BACKEND="QExa20"
export MQSS_HPCQC_ENV=True

t_start_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_start=$(date +%s%3N)
mqssbench run --config config_mqssbench_qaoa_runtimes.yaml
t_end_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_end=$(date +%s%3N)
echo "[SBATCH] $t_start_timestamp: Start execution"
echo "[SBATCH] $t_end_timestamp: Finished execution"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to execute (ms): $((t_end - t_start))"
echo "[SBATCH] -------------------------------------------------"
echo ""

t5_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t5=$(date +%s%3N)
source /home/sw/qis/wolpy/mqss/scripts/unload-mqss-qoffload.sh
t6_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t6=$(date +%s%3N)
echo "[SBATCH] $t5_timestamp: Unloading mqss-qoffload env"
echo "[SBATCH] $t6_timestamp: Finished unloading mqss-qoffload env"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to unload mqss-qoffload env (ms): $((t6 - t5))"
echo "[SBATCH] -------------------------------------------------"
echo ""

