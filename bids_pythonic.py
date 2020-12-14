#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

# For fmriprep-setup
import json
import os, glob, shutil, sys
import subprocess
import logging
import datetime, time
import numpy as np

# For mask, smooth, denoise
from nilearn.input_data import NiftiMasker
from nilearn.image import load_img, resample_img
from nilearn.masking import apply_mask, unmask
import pandas as pd

# For parcellation
from nilearn.image import concat_imgs
from nilearn.input_data import NiftiMapsMasker
from nilearn import datasets


# Check for correct versioning
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")


def create_bids_root(bids_root, description="This is a default description"):
    """ 
    Creates the bids root directory.
  
    Parameters: 
    bids_root(str): path to bids_roots
  
    """

    # Create root directory
    # Create dataset_description.json and README
    if not os.path.isdir(bids_root):
        os.makedirs(bids_root)
        ds_desc =   {
                "Name": description,
                "BIDSVersion": "1.0.1",
                "License": "CC0",
                "Authors": [
                    "Kaustubh Kulkarni",
                    "Daniela Schiller",
                    "Xiaosi Gu"
                ],
                "DatasetDOI": "10.0.2.3/dfjj.10"
                }
        dd_path = f'{bids_root}/dataset_description.json'
        print(dd_path)
        with open(dd_path, 'w') as outfile:
            json.dump(ds_desc, outfile)
        readme_path = f'{bids_root}/README'
        with open(readme_path, 'w') as outfile:
            outfile.write('This is a README. Replace with your README information')
    else:
        print('Root exists! Not overwriting.')


class SetupBIDSPipeline(object):
    """ 
    Setup instance with class methods to create BIDS formatted directory structure.
  
    This class generates the BIDS formatted directory structure.
    Note that the following methods must be run sequentially for successful BIDS directory creation:
    1. validate()
    2. create_bids_hierarchy()
    3. convert()
    4. update_json()

    The bids_pythonic.create_bids_root() method MUST be run before using this class.
  
    """

    def _return_dicom_path(self, dicom_dir, name, pattern, auto_dicom):
        """ 
        Accepts given top-level dicom directory for subjects and given pattern for matching and
        returns a matching dicom directory handling multiple/zero matches.
        Auto-DICOM functionality automatically chooses the directory with the most DICOM files.
      
        Parameters: 
        dicom_dir (str): Root path of all DICOMs
        name (str): subject ID
        anat (str): Regex expression of path to anatomical DICOMs within the root DICOM directory
        func (str): List of regex expressions of paths to function DICOMs within the root DICOM directory
        task (str): Name of functional MRI task

        Returns: 
        str: matching dicom path name    

        """
        match = glob.glob(f"{dicom_dir}/{name}/{pattern}/")
        if len(match) ==1:
            logging.info(f'{pattern} has a match: {match[0]}')
            return match[0]
        elif len(match)>1:
            logging.warning(f'{pattern} has multiple matches!')
            num_dicoms = []
            for i, m in enumerate(match):
                num_files = len(os.listdir(m))
                num_dicoms.append(num_files)
                logging.info(f'{i+1}. {m} has {num_files} files')
            if not auto_dicom:
                ind = int(input('Do you want to use one of these directories? Enter index from above or 0 to exit:  '))
                if ind==0:
                    logging.error(f'{pattern} has multiple matches!\nOutput of glob: {match}\nPlease fix your wildcards.')
                    raise OSError(f'{pattern} has multiple matches!\nOutput of glob: {match}\nPlease fix your wildcards.')
                else:
                    logging.info(f'Using {match[ind-1]}')
                    return match[ind-1]
            else:
                ind = np.argmax(num_dicoms)
                logging.info(f'Auto-DICOM choosing: {match[ind]}')
                return match[ind]
        elif len(match)==0:
            logging.error(f'{pattern} has no matches!\nOutput of glob: {match}\nPlease fix your wildcards.')
            raise OSError(f'{pattern} has no matches!\nOutput of glob: {match}\nPlease fix your wildcards.')
    

    def __init__(self, dicom_dir, name, anat, func, task, root, 
        ignore=False, overwrite=False, auto_dicom=False,
        progress_dir=f'{os.getcwd()}/fpprogress/'):
        """ 
        Constructs the necessary attributes for the SetupBIDSPipeline instance. 
      
        Parameters: 
        dicom_dir (str): Root path of all DICOMs
        name (str): subject ID
        anat (str): Regex expression of path to anatomical DICOMs within the root DICOM directory
        func (str): List of regex expressions of paths to function DICOMs within the root DICOM directory
        task (str): Name of functional MRI task
        root (str): Path to BIDS root that will be created
        ignore (bool): Flag to ignore warning if subject already exists
        overwrite (bool): Flag to remove subject folder if it exists
        progress_dir (str): Path to progress directory to store logging file (TBD)
      
        Returns: 
        obj: SetupBIDSPipeline instance 
      
        """

        ### Create the fmriprepPipeline progress directory if it doesn't exist 
        ### This folder holds the current progress 
        # if not os.path.exists(progress_dir):
        #     os.makedirs(progress_dir)
        # self.progress_dir = progress_dir

        # Configure logging options
        x = datetime.datetime.now()
        timestamp = x.strftime("%m-%d_%H%M")
        #self.logfile = f'{self.progress_dir}/log_{timestamp}.txt'
        logging.basicConfig(format='%(module)s - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)


        # Pdict variable contains all the major variables for BIDS folder setup
        # Field         |           value                                               |
        #-------------------------------------------------------------------------------|
        # name          |   ID of participant                                           |
        # anat          |   Name of anatomical DICOM folder in parent DICOM folder      |
        # func          |   List of functional DICOM folder names in parent DICOM folder|
        # task          |   Name of task                                                |
        # overwrite     |   Delete and overwrite subject folder if it exists            | 
        # ignore        |   Ignore warning if subject folder exists during validation   |

        # Note that for func, if the data is single echo, there is a array of runs

        # Uses glob to match wildcards, but throws error if there are multiple matches
        self.pdict = {}
        self.pdict['root'] = root
        self.pdict['task'] = task

        # Use strip 'sub-' from name if it exists
        # The 'sub-' will be added later for BIDS formatting
        if name.startswith('sub-'):
            self.pdict['name'] = name[4:]
        else:
            self.pdict['name'] = name
        
        # Wildcard matching for anatomical dicom directory name
        self.pdict['anat'] = self._return_dicom_path(dicom_dir, name, anat, auto_dicom=auto_dicom)
        
        # Wildcard matching for functional dicom directory name
        self.pdict['func'] = []
        for one_func in func:
            self.pdict['func'].append(self._return_dicom_path(dicom_dir, name, one_func, auto_dicom=auto_dicom))       
        
        self.pdict['overwrite'] = overwrite
        self.pdict['ignore'] = ignore

        # Initialize paths for BIDS-formatted folders and files
        # anat_path     ->  path to BIDS anat folder
        # func_path     ->  path to BIDS func folder
        # anat_name     ->  filename for BIDS anatomical NIFTI
        # func_name     ->  list of all filenames for BIDS functional NIFTIS
        self.anat_path = ""
        self.func_path = ""
        self.anat_name = ""
        self.func_name = []


    def validate(self):
        """ 
        Validates the presence of BIDS root directory and DICOM folders, 
        and ensures that subject directory doesn't already exist.
      
        """

        logging.info('Validating parameters.....')

        # Validate that BIDS root directory exists!
        # This directory is created by the 'create_bids_root' function below!
        if os.path.isdir(self.pdict['root']):
            logging.info('Root Exists.')
            self.root_exists = True
        else:
            logging.error('Root does not exist!')
            raise OSError('Root does not exist!')
        
        # Check if the subject folder already exists, and will throw an error if it does
        # If overwrite is on, the subject folder will be deleted
        # If ignore is on, the analysis will proceed even if the subject folder exists
        if os.path.isdir(f'{self.pdict["root"]}/sub-{self.pdict["name"]}'):
            if self.pdict['overwrite']:
                logging.warning(f'Overwrite option selected! Removing subject {self.pdict["name"]}')
                shutil.rmtree(f'{self.pdict["root"]}/sub-{self.pdict["name"]}')
            elif self.pdict['ignore']:
                logging.error(f"{self.pdict['name']}' exists! Continuing forward (risky).")
            else:
                logging.error(f"{self.pdict['name']}' exists! Try a different subject name, or ignore/delete existing folder.")
                raise OSError(f"'{self.pdict['name']}' exists! Try a different subject name, or ignore/delete existing folder.")

        # Check that the anatomical DICOM folder exists
        if not os.path.isdir(self.pdict['anat']):
            logging.error(f"'{self.pdict['anat']}' does not exist! Input a valid anatomical DICOM directory.")
            raise OSError(f"'{self.pdict['anat']}' does not exist! Input a valid anatomical DICOM directory.")

        # Check that the functional DICOM folders exist
        for func in self.pdict['func']:
            if not os.path.isdir(func):
                logging.error(f"'{func}' does not exist! Input a valid functional DICOM directory.")
                raise OSError(f"'{func}' does not exist! Input a valid functional DICOM directory.")
        
        # TODO: Validate fmriprep-docker requirements
        # TODO: Validate motion regression requirements

        logging.info('Validated!')


    def create_bids_hierarchy(self):
        """ Creates the subject directory and nested anat and func directories."""

        logging.info('Creating BIDS hierarchy.....')

        # Create subject directory
        # If they do, log an error but continue
        sub_path = f'{self.pdict["root"]}/sub-{self.pdict["name"]}'
        try:
            os.makedirs(sub_path)
        except FileExistsError:
            logging.warning('Subject directory exists!')

        # Create anat and func directories
        # If they do, log an error but continue
        self.anat_path = f'{sub_path}/anat/'
        try:
            os.makedirs(self.anat_path)
        except FileExistsError:
            logging.warning('anat directory exists')

        self.func_path = f'{sub_path}/func/'
        try:
            os.makedirs(self.func_path)
        except FileExistsError:
            logging.warning('func directory exists')

        logging.info("Completed!")


    def convert(self):
        """ 
        Converts the specified DICOMs into NIFTIs using dcm2niix
      
        """

        # Run dcm2niix for anatomical DICOM and rename
        logging.info('Converting anatomical DICOMs to NIFTI and renaming.....')
        self.anat_name = f'sub-{self.pdict["name"]}_T1w'
        command = ['dcm2niix', '-z', 'n', '-f', self.anat_name, '-b', 'y', '-o', self.anat_path, self.pdict['anat']]
        if not os.path.exists(f'{self.anat_path}/{self.anat_name}.nii'):
            print('Running dcm2niix')
            process = subprocess.run(command)
        else:
            logging.warning(f'{self.anat_name} exists! Not overwriting.')
        logging.info('Completed!')

        
        # Run dcm2niix for every functional DICOM and rename
        logging.info('Converting functional DICOMs to NIFTI and renaming.....')
        
        # For single echo data, loop over the self.pdict['func'] array
        run_counter = 1
        for func_input in self.pdict['func']:
            func_name = f'sub-{self.pdict["name"]}_task-{self.pdict["task"]}_run-{str(run_counter)}_bold'
            self.func_name.append(func_name)
            command = ['dcm2niix', '-z', 'n', '-f', func_name, '-b', 'y', '-o', self.func_path, func_input]
            if not os.path.exists(f'{self.func_path}/{func_name}.nii'):
                print('Running dcm2niix')
                process = subprocess.run(command)
            else:
                logging.warning(f'{func_name} exists! Not overwriting.')
            run_counter += 1

        logging.info('Completed!')
    

    def update_json(self):
        """ Updates the JSON sidecars generated with dcm2niix to include a field for TaskName """

        # Add TaskName field to BIDS functional NIFTI sidecars
        logging.info('Updating functional NIFTI sidecars.....')
        for func in self.func_name:
            with open(f'{self.func_path}/{func}.json') as json_file:
                data = json.load(json_file)
                data['TaskName'] = self.pdict["task"]

            with open(f'{self.func_path}/{func}.json', 'w') as outfile:
                json.dump(data,outfile)
        logging.info('Completed!')


def run_fmriprep_docker(bids_root, output, fs_license, freesurfer=False):
    """ 
    Runs the fmriprep-docker command on the BIDS directory generated by SetupBIDSPipeline.
    This command can also be run on an independently generated BIDS directory. 
  
    Parameters: 
    bids_root (str): Path to generated BIDS directory
    output (str): Path to store fmriprep output
    fs_license (str): Path to a valid Freesurfer license
    freesurfer (bool): Flag to specify Freesurfer surface estimation
  
    """

    # This method simply runs the fmriprep-docker command
    logging.info('Executing fmriprep-docker command')
    command = ['fmriprep-docker', bids_root, output, 'participant', '--fs-license-file', fs_license]
    if not freesurfer:
        command.append('--fs-no-reconall')
    #logging.info(command)
    subprocess.run(command)


class FmriprepSingularityPipeline(object):
    """ 
    This class prepares batch scripts and runs fmriprep through a Singularity image.
    Designed for use on Minerva at Mount Sinai.
  
    Note that the following methods must be run in order:
    1. create_singularity_batch()
    2. run_singularity_batch()

    Alternatively, you can run only create_singularity_batch() and submit generated scripts manually. 
  
    """

    def __init__(self, subs, bids_root, output, minerva_options, freesurfer=False, cifti_output=False):
        """ 
        Constructs the necessary attributes for the FmriprepSingularityPipeline instance.   
      
        Parameters: 
        subs (list): List of subject ID strings
        bids_root (str): Path to generated BIDS directory
        output (str): Path to store fmriprep output
        minerva_options (dict): Dictionary of HPC-specific options (see below)
        freesurfer (bool): Flag to specify Freesurfer surface estimation
      
        minerva_options dictionary should contain:
            1. image_location: Path to directory that contains the fmriprep singularity image and Freesurfer license file
            2. batch_dir: Path to a directory to store generated batch scripts
            3. project_dir: Root level project directory (parent to bids_root)

        Returns: 
        obj: FmriprepSingularityPipeline instance 
      
        """

        # Define class variables
        self.subs = subs
        self.bids_root = bids_root
        self.output = output
        self.freesurfer = freesurfer
        self.minerva_options = minerva_options
        self.batch_dir = minerva_options['batch_dir']

    def create_singularity_batch(self):
        """ 
        Creates the subject batch scripts for running fmriprep with Singularity.
        To run in parallel, subjects are run individually and submitted as separate jobs on the cluster.   
      
        """

        logging.info('Setting up fmriprep command through Singularity for Minerva')
        
        # Check if the singularity image exists in the image location
        if not os.path.isfile(f'{self.minerva_options["image_location"]}'):
            logging.error('fmriprep image does not exist in the given location!')
        #     raise OSError('fmriprep image does not exist in the given directory!')

        # Create the specified batch directory folder if it doesn't exist
        logging.info('Creating batch directory for subject scripts')
        if not os.path.isdir(self.batch_dir):
            os.makedirs(self.batch_dir)
        # Create the batchoutput folder within the batch directory folder
        # This will hold the outputs from each of the batch scripts
        if not os.path.isdir(f'{self.batch_dir}/batchoutput'):
            os.makedirs(f'{self.batch_dir}/batchoutput')

        # Loop over all subjects
        for sub in self.subs:

            # Strip the 'sub-' prefix from the subject name string, if it's there
            if sub[:4] == 'sub-':
                sub = sub[4:]

            # Create the subject specific batch script
            sub_batch_script = f'{self.batch_dir}/sub-{sub}.sh'
            with open(sub_batch_script, 'w') as f:
                lines = [
                    # These are the BSUB cookies
                    f'#!/bin/bash\n\n',
                    f'#BSUB -J fmriprep_sub-{sub}\n',
                    f'#BSUB -P acc_guLab\n',
                    f'#BSUB -q private\n',
                    f'#BSUB -n 8\n',
                    f'#BSUB -W 04:00\n',
                    f'#BSUB -R rusage[mem=8000]\n',
                    f'#BSUB -o {self.batch_dir}/batchoutput/nodejob-fmriprep-sub-{sub}.out\n',
                    f'#BSUB -L /bin/bash\n\n',
                    # Module load singularity
                    f'ml singularity/3.6.4\n\n',
                    # Enter the directory that contains the fmriprep.20.0.1.simg
                    f'cd {self.minerva_options["project_dir"]}\n',
                ]
                f.writelines(lines)

                # Create the command
                command = f"singularity run -B $HOME:/home --home /home \
                            -B {os.path.dirname(self.minerva_options['image_location'])}:/software \
                            --cleanenv {self.minerva_options['image_location']} \
                            {self.bids_root} {self.output} participant \
                            --output-spaces MNI152NLin2009cAsym:res-2 \
                            --participant-label {sub} --notrack --fs-license-file /software/license.txt"
                command = " ".join(command.split())
                # Ignore freesurfer if specified
                if not self.freesurfer:
                   command = " ".join([command, '--fs-no-reconall'])
                # Add cifti-output if specified
                if self.cifti_output:
                    command = " ".join([command '--cifti-output'])
                # Output command to batch script
                f.write(command)

        # Include all variables in the 'minerva_option' dictionary
        self.minerva_options['subs'] = self.subs
        self.minerva_options['bids_root'] = self.bids_root
        self.minerva_options['output'] = self.output
        self.minerva_options['freesurfer'] = self.freesurfer

        # Save all parameters within the batch directory as well
        with open(f'{self.batch_dir}/minerva_options.json', 'w') as f:
            json.dump(self.minerva_options, f) 


    def run_singularity_batch(self, subs, overwrite=False):
        """ 
        Submits generated subject batch scripts to the HPC. 
      
        Parameters: 
        subs (list): A list of subject ID strings. May be a subset of subjects in the BIDS directory.
      
        """

        logging.info('Submitting singularity batch scripts to the private queue')
        counter = 1
        for sub in subs:
            # Submit job to scheduler
            if sub.startswith('sub-'):
                sub = sub[4:]
            
            if os.path.isdir(f'{self.output}/sub-{sub}/'):
                logging.warning(f'sub-{sub} preprocessing already completed!')
                if not overwrite:
                    logging.info(f'Skipping sub-{sub}')
                    continue
                else:
                    logging.warning(f'Re-preprocessing sub-{sub}, and overwriting results!')
            logging.info(f'Submitting Job {counter} of {len(subs)}')
            subprocess.run(f'bsub < {self.batch_dir}/sub-{sub}.sh', shell=True)
            counter += 1
            # Sleep for 1 min between job submissions (recommended)
            time.sleep(60)

def get_sub_list(root):
    # Obtain list of all subjects    
    subs = []
    for entry in os.listdir(root):
        if os.path.isdir(os.path.join(root, entry)) and entry.startswith('sub'):
            subs.append(entry)
    return subs

def post_fmriprep_clean_func(root, runs, tasks, output_dir, smoothing=None, chosen_confounds=None):
    """ 
    Global method to brain mask, smooth, and denoise all fMRI output from fmriprep output directory.
    *** STILL IN BETA, USE AT YOUR OWN RISK ***

    Parameters: 
    root (str):                     Base directory of fmriprep output
    runs (int list):                List of all runs to clean
    tasks (str list):               List of task names to clean
    output_dir (str):               Directory to store outputs
    smoothing (int):                FWHM of Gaussian smoothing kernel
    chosen_confounds (str list):    List of confounds used to denoise   

    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    options = {
        'root': root,
        'runs': runs,
        'tasks': tasks,
        'output_dir': output_dir,
        'smoothing': smoothing,
        'chosen_confounds': chosen_confounds
    }
    with open(os.path.join(output_dir, 'options.json'), 'w') as f:
        json.dump(options, f, indent=4)
    
    # Obtain list of all subjects    
    subs = []
    for entry in os.listdir(root):
        if os.path.isdir(os.path.join(root, entry)) and entry.startswith('sub'):
            subs.append(entry)

    # Assuming first subject is representative of full dataset, obtain list of runs
    # runs = []     # TODO

    # Assuming first subject is representative of full dataset, obtain list of tasks
    # tasks = []    # TODO

    # Define postfix depending on options
    postfix = ''
    if smoothing:
        postfix = f'{postfix}_smooth{smoothing}'
    if chosen_confounds:
        postfix = f'{postfix}_denoised'
    postfix = f'{postfix}.nii.gz'

    # Loop over all subjects
    for sub in subs:
        sub_path = os.path.join(output_dir, sub)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)

        # Loop over all tasks and runs
        for task in tasks:
            for run in runs:
                print(f'Working on {sub}, task:{task}, run:{run}')

                # Define patterns for mask, nifti, and confounds vars
                mask_pattern = f'*task-{task}*run-{run}*brain_mask*nii.gz'
                nifti_pattern = f'*task-{task}*run-{run}*preproc_bold*nii*'
                confounds_pattern = f'*task-{task}*run-{run}*confounds*tsv*'

                # Define paths based on patterns
                mask = glob.glob(os.path.join(root, sub, 'func', mask_pattern))[0]
                nifti = glob.glob(os.path.join(root, sub, 'func', nifti_pattern))[0]
                confounds_path = glob.glob(os.path.join(root, sub, 'func', confounds_pattern))[0]

                # Load confounds tsv and create confounds matrix
                if chosen_confounds:
                    confounds = pd.read_csv(confounds_path, sep="\t").fillna(0)
                    confound_matrix = confounds[chosen_confounds].to_numpy()
                    print(f'Confound matrix has shape: {confound_matrix.shape}')
                else:
                    print('No confounds specified')
                    confound_matrix = None

                # Define NiftiMasker, which performs the masking, smoothing and denoising
                masker = NiftiMasker(mask_img=mask, smoothing_fwhm=smoothing, verbose=5)
                masked_data = masker.fit_transform(nifti, confounds=confound_matrix)
                
                # Transform data back into nifti image and save in subject directory
                print('Transforming data back into nifti and saving')
                masked_img = masker.inverse_transform(masked_data)
                mask_img_name = f'{sub}_task-{task}_run-{run}_preproc_bold_mask'
                output_img_name = mask_img_name + postfix
                masked_img.to_filename(os.path.join(sub_path, output_img_name))


def parcellate(location, output_dir=None, parcels=None, is_dir=False, parcel_name='default'):
    """ 
    Global method to parcellate all niftis after mask, smooth, denoise, directory.
    *** STILL IN BETA, USE AT YOUR OWN RISK ***

    Parameters: 
    location (str):                 Base directory of cleaned output
    output_dir (str):               Directory to store outputs
    parcels (int):                  Location of parcels NIFTI, or directory of parcel niftis
    is_dir (bool):                  True if specifying parcel directory
    parcel_name (str):              Name of parcellation  

    """
    for sub in os.listdir(location):
        if not sub.startswith('sub'):
            continue
        for nifti_file in os.listdir(os.path.join(location, sub)):
            if not (nifti_file.endswith('nii') or nifti_file.endswith('nii.gz')):
                continue
            basename = nifti_file.split('.')[0]
            name = f'{basename}_{parcel_name}_rois.tsv'
            nifti = os.path.join(location, sub, nifti_file)

            if parcels:
                # If parcellation is in one file
                if not is_dir:
                    # Create masker
                    masker = NiftiLabelsMasker(labels_img=parcels, standardize='zscore', resampling_target='labels', verbose=5)
                    timeseries = masker.fit_transform(nifti)

                # If parcellation is in separate files within a directory
                elif is_dir:
                    parcel_files = sorted(os.listdir(parcels))
                    atlas_filenames = [os.path.join(parcels, parcel) for parcel in parcel_files]

                    concat_parcels = concat_imgs(atlas_filenames)
                    masker = NiftiMapsMasker(maps_img=concat_parcels, standardize='zscore', resampling_target='maps', verbose=5)
                    timeseries = masker.fit_transform(nifti)

            # If parcellation not specified, use harvard-oxford atlas
            elif not parcels:
                dataset = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
                atlas_filename = dataset.maps

                # Create masker
                masker = NiftiLabelsMasker(labels_img=atlas_filename, standardize='zscore', resampling_target='labels', verbose=5)
                timeseries = masker.fit_transform(nifti)

            # Output time series
            if output_dir:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_path = os.path.join(output_dir, name)
                np.savetxt(output_path, timeseries, delimiter='\t')
            else:
                print(timeseries.shape)

