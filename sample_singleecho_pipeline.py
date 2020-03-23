#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

"""

Here is an example script that utilizes the bids_pythonic module to build the 
BIDS formatted database and execute fmriprep using fmriprep-docker

For local computer use only. You must have dcm2niix and fmriprep-docker installed.

You can adapt this script for your use or build your own.

"""


# Note that the fmriprepPipeline/ folder needs to be added to the PYTHONPATH
#
# Add the command: export PYTHONPATH=${PYTHONPATH}:<location-of-fmriprepPipeline>
# to your ~/.bash_profile file and source it
import bids_pythonic as bp

if __name__ == "__main__":

    # Define your path names
    fs_license = '/Applications/freesurfer/license.txt'
    project_dir = '/Volumes/synapse/home/kulkak01/fmriprepPipeline/'
    bids_root = f"{project_dir}/singleecho_rawdata/bids_root/"
    output_dir = f"{project_dir}/singleecho_rawdata/fmriprep_output/"
    dicom_dir = f"{project_dir}/singleecho_rawdata/dicoms/"

    # Define dicom structure
    # Note that 'func' is a 1D array of dicom folder names for single echo
    multiecho=False
    anat = 'anat'
    func = [ 
        '*sess*1',
        '*sess*2'
    ]

    # Define task name for selected functional data
    task = 'scriptreactivation'

    # Define your list of subjects
    # If 'sub-' is at the start of the subject string, it will be removed
    subs = ['sub-01']

    # This method creates the bids root directory
    bp.create_bids_root(bids_root)

    # Loop over all subjects
    for name in subs:
        setup = bp.SetupBIDSPipeline(dicom_dir, name, anat, func, task, bids_root, ignore=True)
        setup.validate()
        setup.create_bids_hierarchy()
        setup.convert()
        setup.update_json()

    # Run the fmriprep-docker command on the created BIDS directory
    bp.run_fmriprep_docker(bids_root, output_dir, fs_license)
