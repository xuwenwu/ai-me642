#!/bin/bash
#SBATCH --job-name=me642-lammps-demo
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --time=00:10:00
#SBATCH --mem=2G

module load lammps
srun lmp -in sample_input.in
