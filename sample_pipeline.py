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
    project_dir = '/Volumes/synapse/home/kulkak01/fmriprepPipeline/singleecho_rawdata'
    bids_root = f"{project_dir}/rawdata/"
    output_dir = f"{project_dir}/derivatives/"
    dicom_dir = f"{project_dir}/sourcedata/"

    # Define dicom structure
    # Note that 'func' is a 1D array of dicom folder names for single echo
    anat_pattern = 'anat*'
    func_patterns = [ 
        '*sess*1',
        '*sess*2'
    ]

    # Define task name for selected functional data
    task = 'memrecall'

    # Define your list of subjects
    # If 'sub-' is at the start of the subject string, it will be removed
    participants = {
        'participant_id': ['01'],
        'group': [1],
        'test_score': [20.5]
    }

    # Define events for subjects and runs
    # Events is a list of event dictionary objects
    # Each event dictionary object has two fields
    #   - participant_id -> a list of IDs of participants that have this event
    #   - event_properties -> a dictionary with three properties: onset, duration, and trial type
    events = [
        {
            'participant_id': ['01'],
            'event_properties': {
                'onset': [0, 10, 20, 35],
                'duration': [2, 2, 2, 2],
                'trial_type': ['face_a', 'face_b', 'face_a', 'face_b']
            }
        }
    ]

    # Define the minerva options
    image_location = f'/Volumes/synapse/home/kulkak01/software/fmriprep-20.2.0.simg' # where is the fmriprep-20.2.0.simg file located?
    batch_dir = f'{project_dir}/code/batch_dir/' # output directory for all batch scripts
    minerva_options = {
        'image_location': image_location,
        'batch_dir': batch_dir,
        'project_dir': project_dir
    }

    # Create BIDS setup pipeline and execute
    setup = bp.SetupBIDSPipeline(participants, dicom_dir, anat_pattern, func_patterns, task, bids_root)
    setup.create_bids_root()
    setup.validate(overwrite=False, ignore=True)
    setup.obtain_dicoms(auto_dicom=True)
    setup.create_bids_hierarchy()
    setup.create_events(events)
    setup.convert()
    setup.update_json()

    # # Run the fmriprep-docker command on the created BIDS directory
    # bp.run_fmriprep_docker(bids_root, output_dir, fs_license)

    # Run the fmriprep-docker command through Minerva on the created BIDS directory
    fp_singularity = bp.FmriprepSingularityPipeline(participants, bids_root, output_dir, minerva_options, freesurfer=False, cifti_output=False)
    fp_singularity.create_singularity_batch()
    #fp_singularity.run_singularity_batch(subs)
