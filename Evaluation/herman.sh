#!/usr/bin/zsh 

### Job Parameters 
#SBATCH --ntasks=1              # Ask for 8 MPI tasks
#SBATCH --cpus-per-task=1	# One CPU
#SBATCH --time=72:00:00         # Run time of 15 minutes
#SBATCH --job-name=herman  # Sets the job name
#SBATCH --output=/home/er636027/run/results/hermanout.txt     # redirects stdout and stderr to stdout.txt


### Program Code
#module load Python/3.10.4
#module load Java/21.0.5

# cd to the directory where the script lies in
### Change to the work directory
#cd $HOME/run/9.5-stationary-eval || exit


echo "Starting benchmarking."
STARTTIME=$(date +%s)
echo "------------------------------------------------------------"
echo "SLURM JOB NAME: $SLURM_JOB_NAME"
echo "SLURM JOB ID: $SLURM_JOBID"
echo "Running on nodes: $SLURM_NODELIST"
echo "Number of CPUs: $SLURM_CPUS_PER_TASK"
echo "Started at $(date)"
echo "------------------------------------------------------------"

python3 ../scripts/run.py -t stationary -r results -f herman.json

### end of executable commands
ENDTIME=$(date +%s)
DELTA=$(($ENDTIME - $STARTTIME))
DURATION=$(date -d@$DELTA -u +%H:%M:%S)
echo "------------------------------------------------------------"
echo "Finishing at $(date)"
echo "final spent time is $DURATION"
echo "------------------------------------------------------------"
