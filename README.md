# fmriprepPipeline

A Python pipeline for BIDS creation and fmriprep.
From DICOM to BIDS directory structure creation, preprocessing with fmriprep, smoothing and masking with nilearn, motion correction with fmriprep confounds using nilearn.

## Installation

### Docker

Use conda to set up a new isolated environment to install requirements.
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install fmriprep-docker.
Use conda to install dcm2niix.

```bash
pip install --user --upgrade fmriprep-docker
conda install -c conda-forge dcm2niix
```

### Singularity

Use the following command to build the fmriprep singularity image for use in batch scripting

```bash
singularity build /my_images/fmriprep-<version>.simg docker://poldracklab/fmriprep:<version>
```

Note the directory in which the image is located. This is your 'image_directory'.

## Usage

```python
import bids_pythonic as bp

# Define your path names
fs_license = '/path/to/license.txt'
project_dir = '/path/to/project/'
bids_root = f"{project_dir}/rawdata/bids_root/"
output_dir = f"{project_dir}/rawdata/fmriprep_output/"
dicom_dir = f"{project_dir}/rawdata/dicoms/"

# Define dicom structure
anat = 'anat'
func = [ 
    '*sess*1',
    '*sess*2'
]

# Define task name for selected functional data
task = 'example'

# Define your list of participants
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


# Create the SetupBIDSPipeline object
setup = bp.SetupBIDSPipeline(participants, dicom_dir, anat_pattern, func_patterns, task, bids_root)
# Create the bids root directory
setup.create_bids_root()
# Validate DICOMs and path names
setup.validate(overwrite=False, ignore=True)
# Obtain the paths to the DICOM directories/files
setup.obtain_dicoms(auto_dicom=True)
# Initialize BIDS hierarchy
setup.create_bids_hierarchy()
# Use dcm2niix to convert and rename DICOMs to NIFTIs
setup.convert()
# Update the json sidecars for the NIFTI files
setup.update_json()

# Run the fmriprep-docker command on the created BIDS directory
bp.run_fmriprep_docker(bids_root, output_dir, fs_license)
```

Loop over an array of subs to create a `setup` object for each one and run all `setup` object functions. 
`bp.run_fmriprep_docker` only needs to be run once on the BIDS root.
See the sample_singleecho_pipeline.py and sample_multiecho_pipeline.py files for further annotation.

## Parameters

### SetupBIDSPipeline class instance

| Parameter | Function |
| :----: | --- |
| `dicom_dir` | Base folder that contains all anatomical and functional DICOMs |
| `participants` | Dictionary of Subject ID and related properties |
| `anat_pattern` | Regex expression for path to anatomical DICOM folder |
| `func_patterns` | Array of regex expressions for paths to functional DICOMs (see multiecho option for additional information |
| `task` | Task name |
| `root` | Path name for the BIDS root directory you would like to create |
| `ignore=False` | Available for validate method: If ignore is set to True, no error is generated if the subject folder exists in the BIDS root |
| `overwrite=False` | Available for validate method: If overwrite is True, existing subject folders will be deleted in the BIDS root |

### run_fmriprep_docker function

| Parameter | Function |
| :----: | --- |
| `bids_root` | Path to generated BIDS root |
| `output` | Path to fmriprep output that you would like to create |
| `fs_license` | Path to Freesurfer license.txt file |
| `freesurfer=False` | Setting freesurfer to True will utilize the freesurfer option in fmriprep |

### FmriprepSingularity class instance

| Parameter | Function |
| :----: | --- |
| `subs` | List of all subject IDs |
| `bids_root` | Path to generated BIDS root |
| `output` | Path to fmriprep output that you would like to create |
| `minerva_options` | Python dictionary with HPC-specific options |
| `freesurfer=False` | Setting freesurfer to True will utilize the freesurfer option in fmriprep |
| `multiecho=False` | Setting multiecho to True skips BIDS validation and slice timing correction |

Note that the following `minerva_options` dictionary must be created as well

| Parameter | Function |
| :----: | --- |
| `image_location` | Path to the fmriprep.# simg Singularity image |
| `batch_dir` | Path to directory that will contain the batch scripts for HPC |
| `project_dir` | Path to top level directory that contains all the run specific directories |


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Author

* **Kaustubh Kulkarni** - *Development, maintenance* - [More Info](https://kulkarnik.com)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

