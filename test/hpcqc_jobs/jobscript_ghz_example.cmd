#!/bin/sh
#SBATCH -J ghz_example
#SBATCH -o ./%x_%j.out
#SBATCH -e ./%x_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=wolpy
#SBATCH --time=00:05:00

echo "-------------------------------------------------"
echo "Loading the mqss env"
echo "-------------------------------------------------"
t0_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t0=$(date +%s%3N)
source /home/sw/qis/wolpy/mqss/scripts/load-mqss-qoffload.sh
t1_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t1=$(date +%s%3N)
echo "$t0_timestamp: Start loading mqss env"
echo "$t1_timestamp: Finished loading mqss env"
source ~/export_conda_env.sh
t2=$(date +%s%3N)
echo "-------------------------------------------------"
echo "Elapsed time to load mqss env (ms): $((t1 - t0))"
echo "Elapsed time to load conda env (ms): $((t2 - t1))"
echo "-------------------------------------------------"

export MQSS_HPCQC_ENV=True
t_start_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_start=$(date +%s%3N)
~/conda/x86_64/bin/python ghz_example.py --backend=QExa20
t_end_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t_end=$(date +%s%3N)
echo "$t_start_timestamp: Start execution"
echo "$t_end_timestamp: Finished execution"
echo "-------------------------------------------------"
echo "Elapsed time to execute (ms): $((t_end - t_start))"
echo "-------------------------------------------------"


echo "-------------------------------------------------"
echo "Unloading the mqss env"
echo "-------------------------------------------------"
t3_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t3=$(date +%s%3N)
source /home/sw/qis/wolpy/mqss/scripts/unload-mqss-qoffload.sh
t4_timestamp=$(date +"%a %d-%m-%Y %H:%M:%S.%3N")
t4=$(date +%s%3N)
echo "$t3_timestamp: Start unloading mqss env"
echo "$t4_timestamp: Finished unloading mqss env"
echo "-------------------------------------------------"
echo "Elapsed time to unload mqss env (ms): $((t4 - t3))"
echo "-------------------------------------------------"
