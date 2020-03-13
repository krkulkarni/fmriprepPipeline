#!/bin/bash

#BSUB -J fmriprep_sub-01
#BSUB -P acc_guLab
#BSUB -q private
#BSUB -n 4
#BSUB -W 20:00
#BSUB -R rusage[mem=16000]
#BSUB -o /Volumes/synapse/home/kulkak01/fmriprepPipeline//batch_dir/batchoutput/nodejob-fmriprep-sub-01.out
#BSUB -L /bin/bash

ml singularity/3.2.1

cd /Volumes/synapse/home/kulkak01/fmriprepPipeline/
singularity run --home /hpc/home/kulkak01/ --cleanenv fmriprep-20.0.1.simg /Volumes/synapse/home/kulkak01/fmriprepPipeline//rawdata/bids_root/ /Volumes/synapse/home/kulkak01/fmriprepPipeline//rawdata/fmriprep_output/ participant --participant-label 01 --notrack --fs-license-file /Applications/freesurfer/license.txt --fs-no-reconall