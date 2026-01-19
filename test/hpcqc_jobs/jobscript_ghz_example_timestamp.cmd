#!/bin/sh
#SBATCH -J ghz_example_timestamp
#SBATCH -o ./%x_%j.out
#SBATCH -e ./%x_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=wolpy
#SBATCH --time=00:05:00

t1_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t1=$(date +%s%3N)
source ~/export_conda_env.sh
t2_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t2=$(date +%s%3N)
echo "[SBATCH] $t1_timestamp: Start loading conda env"
echo "[SBATCH] $t2_timestamp: Finished loading conda env"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to load conda env (ms): $((t2 - t1))"
echo "[SBATCH] -------------------------------------------------"

t_start_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_start=$(date +%s%3N)
~/conda/x86_64/bin/python ghz_example_timestamp.py --backend=QExa20
t_end_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_end=$(date +%s%3N)
echo "[SBATCH] $t_start_timestamp: Start execution"
echo "[SBATCH] $t_end_timestamp: Finished execution"
echo "[SBATCH] -------------------------------------------------"
echo "[SBATCH] Elapsed time to execute (ms): $((t_end - t_start))"
echo "[SBATCH] -------------------------------------------------"
