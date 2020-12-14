#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Dec 12, 2020

"""

Here is an example script that utilizes the post_fmriprep_clean module to clean the
fmriprep output

You can adapt this script for your use or build your own.

"""


# Note that the fmriprepPipeline/ folder needs to be added to the PYTHONPATH
#
# Add the command: export PYTHONPATH=${PYTHONPATH}:<location-of-fmriprepPipeline>
# to your ~/.bash_profile file and source it
import bids_pythonic as bp
import os

if __name__ == "__main__":

    # Define your path names
    project_dir = '/Volumes/synapse/home/kulkak01/BIDS_MultiEcho/'
    fmriprep_dir = os.path.join(project_dir, 'fmriprep_no_reconall/fmriprep')
    output_dir = os.path.join(project_dir, 'fmriprep_no_reconall/post_fmriprep_')

    # See https://fmriprep.org/en/stable/outputs.html#confounds for list of all confounds
    # Suggested confounds included here
    chosen_confounds = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z',
    					'a_comp_cor_00', 'a_comp_cor_01', 'a_comp_cor_02', 
    					'a_comp_cor_03', 'a_comp_cor_04', 'a_comp_cor_05', 
    					'cosine00', 'cosine01', 'cosine02', 'cosine03', 'cosine04', 'cosine05',
    					'framewise_displacement']

    postfp = bp.post_fmriprep_clean_func(root=fmriprep_dir, 
    	runs=[1], 
    	tasks=['fish', 'slot'], 
    	output_dir=output_dir,
    	smoothing=4, 
    	chosen_confounds=chosen_confounds
    	)

