#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

import bids_pythonic as bp

if __name__ == "__main__":
    
    params = {
        "name": "1403",
        "description": "This is the description",
        "root": "bids_root/",
        "anat": "dicoms/anat_dicom/",
        "func": [
            "dicoms/session1/",
            "dicoms/session2/"
        ],
        "task": "recall",
        "overwrite": "true"
    }

    pipeline = bp.FmriprepPipeline(params)
    pipeline.validate()
    pipeline.create_bids_hierarchy()
    pipeline.convert()
    pipeline.update_json()

    
    pipeline.run_fmriprep()
    pipeline.motionreg()