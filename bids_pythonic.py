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

class SetupBIDSPipeline(object):

    def __init__(self, params, pipeline_dir=os.getcwd(), singularity_batch_created=False, root_exists=False):
        if not os.path.exists(pipeline_dir):
            os.makedirs(pipeline_dir)
        self.pipeline_dir = pipeline_dir

        x = datetime.datetime.now()
        timestamp = x.strftime("%m-%d_%H%M")
        self.logfile = f'{self.pipeline_dir}/log_{timestamp}.txt'
        logging.basicConfig(format='%(module)s - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

        self.pdict = params
        self.root_exists = root_exists
        self.anat_path = ""
        self.func_path = ""
        self.anat_name = ""
        self.func_name = []

        self.singularity_batch_created = singularity_batch_created
            

    def validate(self, multiecho=False):
        logging.info('Validating parameters.....')

        # Validate parameters dictionary
        root_path = self.pdict['root']
        if os.path.isdir(root_path):
            logging.warning('Root Exists! Not overwriting.')
            self.root_exists = True
        
        if os.path.isdir(f'{self.pdict["root"]}/sub-{self.pdict["name"]}'):
            if self.pdict['overwrite'] == 'true':
                logging.warning(f'Overwrite option selected! Removing subject {self.pdict["name"]}')
                shutil.rmtree(f'{self.pdict["root"]}/sub-{self.pdict["name"]}')
            else:
                logging.error(f"{self.pdict['name']}' exists! Try a different subject name, or delete existing folder.")
                raise OSError(f"'{self.pdict['name']}' exists! Try a different subject name, or delete existing folder.")

        if not os.path.isdir(self.pdict['anat']):
            logging.error(f"'{self.pdict['anat']}' does not exist! Input a valid anatomical DICOM directory.")
            raise OSError(f"'{self.pdict['anat']}' does not exist! Input a valid anatomical DICOM directory.")

        for func in self.pdict['func']:
            if not multiecho:
                if not os.path.isdir(func):
                    logging.error(f"'{func}' does not exist! Input a valid functional DICOM directory.")
                    raise OSError(f"'{func}' does not exist! Input a valid functional DICOM directory.")
            elif multiecho:
                if not "echo" in func:
                    logging.error(f"'Echo' key does not exist in params! See documentation for multiecho.")
                for echo in func['echo']:
                    if not os.path.isdir(echo):
                        logging.error(f"'{echo}' does not exist! Input a valid functional DICOM directory.")
                        raise OSError(f"'{echo}' does not exist! Input a valid functional DICOM directory.")
    
        # Validate fmriprep-docker requirements

        # Validate motion regression requirements

        logging.info('Validated!')


    def create_bids_hierarchy(self):
        logging.info('Creating BIDS hierarchy.....')

        # Create root directory
        # Create dataset_description.json and README
        if not self.root_exists:
            os.makedirs(self.pdict['root'])
            ds_desc =   {
                    "Name": self.pdict['description'],
                    "BIDSVersion": "1.0.1",
                    "License": "CC0",
                    "Authors": [
                        "Kaustubh Kulkarni",
                        "Matt Schafer"
                    ],
                    "DatasetDOI": "10.0.2.3/dfjj.10"
                    }
            dd_path = f'{self.pdict["root"]}/dataset_description.json'
            with open(dd_path, 'w') as outfile:
                json.dump(ds_desc, outfile)
            readme_path = f'{self.pdict["root"]}/README'
            with open(readme_path, 'w') as outfile:
                outfile.write('This is a README')

        # Create subject directory
        sub_path = f'{self.pdict["root"]}/sub-{self.pdict["name"]}'
        try:
            os.makedirs(sub_path)
        except FileExistsError:
            logging.warning('sub directory exists!')

        # Create anat and func directories (if in params)
        if self.pdict['anat']:
            self.anat_path = f'{sub_path}/anat/'
            try:
                os.makedirs(self.anat_path)
            except FileExistsError:
                logging.warning('anat directory exists')

        if self.pdict['func']:
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
        #print(command)
        print(f'{self.anat_path}/{self.anat_name}.nii')
        if not os.path.exists(f'{self.anat_path}/{self.anat_name}.nii'):
            process = subprocess.run(command)
            print('Running dcm2niix')
        else:
            logging.warning(f'{self.anat_name} exists! Not overwriting.')
        logging.info('Completed!')

        
        # Run dcm2niix for every functional DICOM and rename
        logging.info('Converting functional DICOMs to NIFTI and renaming.....')
        if not multiecho:
            run_counter = 1
            for func_input in self.pdict['func']:
                func_name = f'sub-{self.pdict["name"]}_task-{self.pdict["task"]}_run-{str(run_counter)}_bold'
                self.func_name.append(func_name)
                command = ['dcm2niix', '-z', 'n', '-f', func_name, '-b', 'y', '-o', self.func_path, func_input]
                #print(command)
                process = subprocess.run(command)
                run_counter += 1
        elif multiecho:
            run_counter = 1
            for func_input in self.pdict['func']:
                echo_counter = 1
                for echo_input in func_input['echo']:
                    echo_name = f'sub-{self.pdict["name"]}_task-{self.pdict["task"]}_run-{str(run_counter)}_echo-{str(echo_counter)}_bold'
                    self.func_name.append(echo_name)
                    command = ['dcm2niix', '-z', 'n', '-f', 'temp', '-b', 'y', '-o', self.func_path, echo_input]
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


class FmriprepDockerPipeline(object):

    def __init__(self):
        pass

    @classmethod
    def run_fmriprep(self, subs, bids_root, output, fs_license, freesurfer=False):
        # Run fmriprep-docker command
        logging.info('Executing fmriprep-docker command')
        command = ['fmriprep-docker', bids_root, output, 'participant', '--fs-license-file', fs_license]
        if not freesurfer:
            command.append('--fs-no-reconall')
        logging.info(command)
        subprocess.run(command)

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
                subprocess.run(f'bsub