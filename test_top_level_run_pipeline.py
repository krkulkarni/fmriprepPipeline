#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

import bids_pythonic as bp

if __name__ == "__main__":
    
    fs_license = '/Applications/freesurfer/license.txt'
    project_dir = '/Volumes/synapse/home/kulkak01/fmriprepPipeline/'
    bids_root = f"{project_dir}/rawdata/bids_root/"
    output_dir = f"{project_dir}/rawdata/fmriprep_output/"
    dicom_dir = f"{project_dir}/rawdata/dicoms/"
    subs = ['01']

    minerva_options = {
        'image_directory': f'{project_dir}',
        'batch_dir': f'{project_dir}/batch_dir',
        'hpc_home': '/hpc/home/kulkak01/',

    }

    for s in subs:
        params = {
            "name": s,
            "description": "This is the description",
            "root": bids_root,
            "anat": f"{dicom_dir}/{s}/anat/",
            "func": [
                f"{dicom_dir}/{s}/session2/"
            ],
            "task": "scriptreactivation",
            "overwrite": "true"
        }

        pipeline = bp.FmriprepPipeline(params)
        pipeline.validate()
        pipeline.create_bids_hierarchy()
        pipeline.convert()
        pipeline.update_json()

    fpsing = bp.FmriprepSingularityPipeline(subs, bids_root, output_dir, fs_license, freesurfer=False, minerva_options=minerva_options)
    fpsing.create_singularity_batch()
    fpsing.run_singularity_batch()
    bp.motionreg(subs)