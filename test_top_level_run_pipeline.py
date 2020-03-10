#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

import bids_pythonic as bp

if __name__ == "__main__":
    
    fs_license = '/Applications/freesurfer/license.txt'
    project_dir = '/Volumes/synapse/home/kulkak01/fmriprepPipeline/'
    bids_root = f"{project_dir}/bids_root/"
    output_dir = f"{project_dir}/fmriprep_output/"
    dicom_dir = f"{project_dir}/dicoms/"
    subs = ['01']

    minerva_options = {
        'image_directory': '.',
        'batch_dir': '.',
        'hpc_home': '/hpc/home/kulkak01/',

    }

    # for s in subs:
    #     params = {
    #         "name": s,
    #         "description": "This is the description",
    #         "root": bids_root,
    #         "anat": f"{dicom_dir}/{s}/anat/",
    #         "func": [
    #             f"{dicom_dir}/{s}/session2/"
    #         ],
    #         "task": "scriptreactivation",
    #         "overwrite": "true"
    #     }

    #     pipeline = bp.FmriprepPipeline(params)
    #     pipeline.validate()
    #     pipeline.create_bids_hierarchy()
    #     pipeline.convert()
    #     pipeline.update_json()

    bp.run_fmriprep(subs, bids_root, output_dir, fs_license, minerva=True, minerva_options=minerva_options)
    bp.motionreg(subs)