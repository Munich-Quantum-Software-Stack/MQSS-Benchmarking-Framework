#!/bin/sh
#SBATCH -J ghz_example
#SBATCH -o ./%x_%j.out
#SBATCH -e ./%x_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=wolpy
#SBATCH --time=00:05:00

echo '---------------------------------'
echo 'Loading the mqss env'
echo '---------------------------------'
t0=$(date +%s%N)
source /home/sw/qis/wolpy/mqss/scripts/load-mqss-qoffload.sh
t1=$(date +%s%N)
source ~/export_conda_env.sh
t2=$(date +%s%N)
echo "Time to load mqss env (ms): $((t1 - t0))"
echo "Time to load conda env (ms): $((t2 - t1))"

export MQSS_HPCQC_ENV=True
t_start=$(date +%s%N)
~/conda/x86_64/bin/python ghz_example.py --backend=QExa20
t_end=$(date +%s%N)
echo "Total execution time (ms): $((t_end - t_start))"

echo '---------------------------------'
echo 'Unloading the mqss env'
echo '---------------------------------'
t3=$(date +%s%N)
source /home/sw/qis/wolpy/mqss/scripts/unload-mqss-qoffload.sh
t4=$(date +%s%N)
echo "Time to unload mqss env (ms): $((t4 - t3))"
