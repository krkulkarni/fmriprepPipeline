#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

"""

Here is an example script that utilizes the bids_pythonic module 
to build the BIDS formatted database and execute fmriprep using either
fmriprep-docker (for local usage) or singularity (minerva usage)

Examples of both single echo and multi echo are shown.

You can adapt this script for your use or build your own.

"""


import bids_pythonic as bp

if __name__ == "__main__":


    # Define your path names
    fs_license = '/Applications/freesurfer/license.txt'
    project_dir = '/Volumes/synapse/home/kulkak01/fmriprepPipeline/'
    bids_root = f"{project_dir}/multiecho_rawdata/bids_root/"
    output_dir = f"{project_dir}/multiecho_rawdata/fmriprep_output/"
    dicom_dir = f"{project_dir}/multiecho_rawdata/dicoms/"
    subs = ['sub-02']

    # Define dicom structure
    # Note that 'func' is a 2D list of lists, of all echos for each run
    anat = 'anat'
    func = [ 
        [
            'task-fish_run-1_echo-1',
            'task-fish_run-1_echo-2'
        ]
    ]

    # Define your task name
    task = 'fish'

    # Define the minerva options
    # minerva_options = {
    #     'image_directory': f'{project_dir}',
    #     'batch_dir': f'{project_dir}/batch_dir',
    #     'hpc_home': '/hpc/home/kulkak01/',

    # }

    bp.create_bids_root(bids_root)

    for name in subs:
        setup = bp.SetupBIDSPipeline(dicom_dir, name, anat, func, task, bids_root, ignore=True, multiecho=True)
        setup.validate(multiecho=True)
        setup.create_bids_hierarchy()
        setup.convert(multiecho=True)
        setup.update_json()

    #fpsing = bp.FmriprepSingularityPipeline(subs, bids_root, output_dir, fs_license, freesurfer=False, minerva_options=minerva_options)
    #fpsing.create_singularity_batch()
    #fpsing.run_singularity_batch()
    #bp.motionreg(subs)