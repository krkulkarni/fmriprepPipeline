#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

import bids_pythonic as bp

if __name__ == "__main__":
    
    project_dir = '/Volumes/synapse/home/kulkak01/BIDS_ScriptReactivation/'
    bids_root = f"{project_dir}/rawdata/raw_nifti/"
    dicom_dir = f"{project_dir}/rawdata/Dicom/"
    subs = ['008', '1223', '1253', '1263', '1293', '1307', '1315', '1322', '1339', '1343','1351','1356','1364','1369','1390','1464']

    for s in subs:
        params = {
            "name": s,
            "description": "This is the description",
            "root": bids_root,
            "anat": f"{dicom_dir}/{s}/anat/",
            "func": [
                f"{dicom_dir}/{s}/func/"
            ],
            "task": "scriptreactivation",
            "overwrite": "false"
        }

        pipeline = bp.FmriprepPipeline(params)
        pipeline.validate()
        pipeline.create_bids_hierarchy()
        pipeline.convert()
        pipeline.update_json()


        pipeline.run_fmriprep()
        pipeline.motionreg()