#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

import argparse
import json
import os, glob
import subprocess
import shutil
import logging
import datetime
import time


def create_bids_root(bids_root, description="This is a default description"):
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
                    "Matt Schafer"
                ],
                "DatasetDOI": "10.0.2.3/dfjj.10"
                }
        dd_path = f'{bids_root}/dataset_description.json'
        print(dd_path)
        with open(dd_path, 'w') as outfile:
            json.dump(ds_desc, outfile)
        readme_path = f'{bids_root}/README'
        with open(readme_path, 'w') as outfile:
            outfile.write('This is a README')
    else:
        print('Root exists! Not overwriting.')

        
class SetupBIDSPipeline(object):

    #
    # This class accepts parameters (listed below), a directory for progress files
    #
    
    def __init__(self, dicom_dir, name, anat, func, task, root, 
        multiecho=False, ignore=False, overwrite=False, progress_dir=f'{os.getcwd()}/fpprogress/'):
        
        ### Create the fmriprepPipeline progress directory if it doesn't exist 
        ### This folder holds the current progress 
        # if not os.path.exists(progress_dir):
        #     os.makedirs(progress_dir)
        # self.progress_dir = progress_dir

        # Strip 'sub-' from name
        if name[:4] == 'sub-':
            name = name[4:]

        # Pdict variable contains all the major variables for BIDS folder setup
        # Field         |           value                                               |
        #-------------------------------------------------------------------------------|
        # name          |   ID of participant                                           |
        # anat          |   Name of anatomical DICOM folder in parent DICOM folder      |
        # func          |   List of functional DICOM folder names in parent DICOM folder|
        # task          |   Name of task                                                |
        # multiecho     |   Flag for multi-echo data                                    |
        # overwrite     |   Delete and overwrite subject folder if it exists            | 
        # ignore        |   Ignore warning if subject folder exists during validation   |

        # Note that for func, if the data is single echo, there is a array of runs
        # and for multiecho data it is an array of arrays of echoes for each run
        self.pdict = {}
        self.pdict['root'] = root
        self.pdict['name'] = name
        self.pdict['anat'] = f"{dicom_dir}/{name}/{anat}/"
        self.pdict['task'] = task
        self.pdict['multiecho'] = multiecho
        if not multiecho:
            self.pdict['func'] = [f"{dicom_dir}/{name}/{one_func}/" for one_func in func]
        elif multiecho:
            self.pdict['func'] = []
            for run in func:
                run_arr = [f"{dicom_dir}/{name}/{one_func}/" for one_func in run]
                self.pdict['func'].append(run_arr)
        self.pdict['overwrite'] = overwrite
        self.pdict['ignore'] = ignore


        # Create the logging file in the progress directory
        x = datetime.datetime.now()
        timestamp = x.strftime("%m-%d_%H%M")
        self.logfile = f'{self.progress_dir}/log_{timestamp}.txt'
        logging.basicConfig(format='%(module)s - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

        # Initialize paths for BIDS-formatted folders and files
        # anat_path     ->  path to BIDS anat folder
        # func_path     ->  path to BIDS func folder
        # anat_name     ->  filename for BIDS anatomical NIFTI
        # func_name     ->  list of all filenames for BIDS functional NIFTIS
        self.anat_path = ""
        self.func_path = ""
        self.anat_name = ""
        self.func_name = []


    def validate(self, multiecho=False):
        logging.info('Validating parameters.....')

        # Validate that BIDS root directory exists!
        # This directory is created by the 'create_bids_root' function below!
        if os.path.isdir(self.pdict['root']):
            logging.warning('Root Exists!')
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
                logging.error(f"{self.pdict['name']}' exists! Try a different subject name, or delete existing folder.")
                raise OSError(f"'{self.pdict['name']}' exists! Try a different subject name, or delete existing folder.")

        # Check that the anatomical DICOM folder exists
        if not os.path.isdir(self.pdict['anat']):
            logging.error(f"'{self.pdict['anat']}' does not exist! Input a valid anatomical DICOM directory.")
            raise OSError(f"'{self.pdict['anat']}' does not exist! Input a valid anatomical DICOM directory.")

        # Check that the functional DICOM folders exist
        if not multiecho:
            for func in self.pdict['func']:
                if not os.path.isdir(func):
                    logging.error(f"'{func}' does not exist! Input a valid functional DICOM directory.")
                    raise OSError(f"'{func}' does not exist! Input a valid functional DICOM directory.")
        elif multiecho:
            for run in self.pdict['func']:
                for echo in run:
                    if not os.path.isdir(echo):
                        logging.error(f"'{echo}' does not exist! Input a valid functional DICOM directory.")
                        raise OSError(f"'{echo}' does not exist! Input a valid functional DICOM directory.")

        # TODO: Validate fmriprep-docker requirements
        # TODO: Validate motion regression requirements

        logging.info('Validated!')


    def create_bids_hierarchy(self):
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


    def convert(self, multiecho=False):
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
        if not multiecho:
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

        # For multi echo data, there is a list of runs, and each run is a list of echos
        # Loop over the array of arrays and rename appropriately
        # All outputs are in the BIDS func directory, but the run-# and echo-# are different
        # Note: dcm2niix outputs multiecho weirdly, so they are first named temp, and converted to the right name
        elif multiecho:
            run_counter = 1
            for run in self.pdict['func']:
                echo_counter = 1
                for echo in run:
                    echo_name = f'sub-{self.pdict["name"]}_task-{self.pdict["task"]}_run-{str(run_counter)}_echo-{str(echo_counter)}_bold'
                    self.func_name.append(echo_name)
                    command = ['dcm2niix', '-z', 'n', '-f', 'temp', '-b', 'y', '-o', self.func_path, echo]
                    #print(command)
                    if not os.path.exists(f'{self.func_path}/{echo_name}.nii'):
                        process = subprocess.run(command)
                        to_rename = glob.glob(f"{self.func_path}*temp*.nii")[0]
                        os.rename(to_rename, f'{self.func_path}/{echo_name}.nii')
                        to_rename = glob.glob(f"{self.func_path}*temp*.json")[0]
                        os.rename(to_rename, f'{self.func_path}/{echo_name}.json') 
                    else:
                        logging.warning(f'{echo_name} exists! Not overwriting.')
                    echo_counter += 1
                run_counter += 1
        logging.info('Completed!')
    

    def update_json(self):
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
    # This method simply runs the fmriprep-docker command
    logging.info('Executing fmriprep-docker command')
    command = ['fmriprep-docker', bids_root, output, 'participant', '--fs-license-file', fs_license]
    if not freesurfer:
        command.append('--fs-no-reconall')
    logging.info(command)
    #subprocess.run(command)


class FmriprepSingularityPipeline(object):

    def __init__(self, subs, bids_root, output, fs_license, freesurfer, minerva_options, singularity_batch_created=False, multiecho=False):
        self.subs = subs
        self.bids_root = bids_root
        self.output = output
        self.fs_license = fs_license
        self.freesurfer = freesurfer
        self.minerva_options = minerva_options
        self.batch_dir = minerva_options['batch_dir']
        self.singularity_batch_created = singularity_batch_created
        self.multiecho = multiecho

    def create_singularity_batch(self):
        logging.info('Setting up fmriprep command through Singularity for Minerva')
        
        # if not os.path.isfile(f'{minerva_options["image_directory"]}/fmriprep-20.0.1.simg'):
        #     logging.error('fmriprep image does not exist in the given directory!')
        #     raise OSError('fmriprep image does not exist in the given directory!')

        logging.info('Creating batch directory for subject scripts')
        if not os.path.isdir(self.batch_dir):
            os.makedirs(self.batch_dir)
        if not os.path.isdir(f'{self.batch_dir}/batchoutput'):
            os.makedirs(f'{self.batch_dir}/batchoutput')

        for sub in self.subs:
            sub_batch_script = f'{self.batch_dir}/sub-{sub}.sh'
            with open(sub_batch_script, 'w') as f:
                lines = [
                f'#!/bin/bash\n\n',
                f'#BSUB -J fmriprep_sub-{sub}\n',
                f'#BSUB -P acc_guLab\n',
                f'#BSUB -q private\n',
                f'#BSUB -n 4\n',
                f'#BSUB -W 20:00\n',
                f'#BSUB -R rusage[mem=16000]\n',
                f'#BSUB -o {self.batch_dir}/batchoutput/nodejob-fmriprep-sub-{sub}.out\n',
                f'#BSUB -L /bin/bash\n\n',
                f'ml singularity/3.2.1\n\n',
                f'cd {self.minerva_options["image_directory"]}\n',
                ]
                f.writelines(lines)

                command = f'singularity run --home {self.minerva_options["hpc_home"]} --cleanenv fmriprep-20.0.1.simg {self.bids_root} {self.output} participant --participant-label {sub} --notrack --fs-license-file {self.fs_license}'
                if not self.freesurfer:
                   command = " ".join([command, '--fs-no-reconall'])
                f.write(command)
                if multiecho:
                    command = " ".join([command, '--ignore slicetiming'])

        self.minerva_options['subs'] = self.subs
        self.minerva_options['bids_root'] = self.bids_root
        self.minerva_options['output'] = self.output
        self.minerva_options['freesurfer'] = self.freesurfer

        with open(f'{self.batch_dir}/minerva_options.json', 'w') as f:
            json.dump(self.minerva_options, f) 

        self.singularity_batch_created = True


    def run_singularity_batch(self):
        logging.info('Submitting singularity batch scripts to the private queue')
        if self.singularity_batch_created:
            for sub in self.subs:
                subprocess.run(f'bsub < {self.batch_dir}/sub-{sub}.sh')
                time.sleep(60)


def motionreg(subs):
    # Run either GLM regression or ART repair for motion
    pass
