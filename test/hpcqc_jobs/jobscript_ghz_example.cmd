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
source /home/sw/qis/wolpy/mqss/scripts/load-mqss-qoffload.sh
source ~/export_conda_env.sh

export MQSS_HPCQC_ENV=True

~/conda/x86_64/bin/python ghz_example.py --backend=QExa20

echo '---------------------------------'
echo 'Unloading the mqss env'
echo '---------------------------------'
source /home/sw/qis/wolpy/mqss/scripts/unload-mqss-qoffload.sh
