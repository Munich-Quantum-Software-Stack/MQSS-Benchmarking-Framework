#!/bin/sh
#SBATCH -J ghz_example
#SBATCH -o ./%x_%j.out
#SBATCH -e ./%x_%j.err
#SBATCH --ntasks=1
#SBATCH --gres=qpu:1
#SBATCH --cpus-per-task=1
#SBATCH --partition=wolpy
#SBATCH --time=00:20:00


t0_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t0=$(date +%s%3N)
source /home/sw/qis/wolpy/mqss/scripts/load-mqss-qoffload.sh
t1_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t1=$(date +%s%3N)
echo "[SBATCH] $t0_timestamp: Start loading mqss-qoffload env"
echo "[SBATCH] $t1_timestamp: Finished loading mqss-qoffload env"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to load mqss-qoffload env (ms): $((t1 - t0))"
echo "[SBATCH] -------------------------------------------------"
echo ""

module use -p /home/sw/qis/wolpy/hpcqc-software/modules/linux-rocky9-icelake/
##module load python/3.11.7-gcc-11.4.1-o75q74w
##module load py-qiskit
##module load py-mqss-qiskit
##nc -zv localhost 5672

t2_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t2=$(date +%s%3N)
source ~/export_conda_env.sh
t3_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t3=$(date +%s%3N)
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to load user-conda env (ms): $((t3 - t2))"
echo "[SBATCH] -------------------------------------------------"
echo ""

export MQSS_HPCQC_ENV=True
t_start_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_start=$(date +%s%3N)
~/conda/x86_64/bin/python ghz_example.py --backend=QExa20
t_end_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_end=$(date +%s%3N)
echo "[SBATCH] $t_start_timestamp: Start execution"
echo "[SBATCH] $t_end_timestamp: Finished execution"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to execute (ms): $((t_end - t_start))"
echo "[SBATCH] -------------------------------------------------"
echo ""

t3_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t3=$(date +%s%3N)
source /home/sw/qis/wolpy/mqss/scripts/unload-mqss-qoffload.sh
t4_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t4=$(date +%s%3N)
echo "[SBATCH] $t3_timestamp: Unloading mqss-qoffload env"
echo "[SBATCH] $t4_timestamp: Finished unloading mqss-qoffload env"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to unload mqss-qoffload env (ms): $((t4 - t3))"
echo "[SBATCH] -------------------------------------------------"
echo ""
