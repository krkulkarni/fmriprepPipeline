#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

import argparse
import json
import os
import subprocess
import shutil

class FmriprepPipeline(object):

    def __init__(self):
        self.pdict = None
        self.root_exists = False
        self.anat_path = ""
        self.func_path = ""
        self.anat_name = ""
        self.func_name = []


    def read_json(self, param_path):
        try:
            with open(param_path) as json_file:
                self.pdict = json.load(json_file)
        except FileNotFoundError:
            raise FileNotFoundError(f'\'{args.parameters}\' does not exist. Please try again with a valid parameters file.')


    def validate(self):
        print('Validating parameters.....', end='')

        # Validate parameters dictionary
        root_path = self.pdict['root']
        if os.path.isdir(root_path):
            self.root_exists = True
        
        if os.path.isdir(f'{self.pdict["root"]}/sub-{self.pdict["name"]}'):
            if self.pdict['overwrite'] == 'true':
                shutil.rmtree(f'{self.pdict["root"]}/sub-{self.pdict["name"]}')
            else:
                raise OSError(f"'{self.pdict['name']}' exists! Try a different subject name, or delete existing folder.")

        if not os.path.isdir(self.pdict['anat']):
            raise OSError(f"'{self.pdict['anat']}' does not exist! Input a valid anatomical DICOM directory.")

        for func in self.pdict['func']:
            if not os.path.isdir(func):
                raise OSError(f"'{func}' does not exist! Input a valid functional DICOM directory.")
    
        # Validate fmriprep-docker requirements

        # Validate motion regression requirements

        print('Validated!')


    def create_bids_hierarchy(self):
        print('Creating BIDS hierarchy.....', end='')

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
        os.makedirs(sub_path)

        # Create anat and func directories (if in params)
        if self.pdict['anat']:
            self.anat_path = f'{sub_path}/anat/'
            os.makedirs(self.anat_path)

        if self.pdict['func']:
            self.func_path = f'{sub_path}/func/'
            os.makedirs(self.func_path)

        print ("Completed!")

    def convert(self):
        # Run dcm2niix for anatomical DICOM and rename
        self.anat_name = f'sub-{self.pdict["name"]}_T1w'
        command = ['dcm2niix', '-z', 'n', '-f', self.anat_name, '-b', 'y', '-o', self.anat_path, self.pdict['anat']]
        #print(command)
        process = subprocess.run(command)


        # Run dcm2niix for every functional DICOM and rename
        run_counter = 1
        for func_input in self.pdict['func']:
            func_name = f'sub-{self.pdict["name"]}_task-{self.pdict["task"]}_run-{str(run_counter)}_bold'
            self.func_name.append(func_name)
            command = ['dcm2niix', '-z', 'n', '-f', func_name, '-b', 'y', '-o', self.func_path, func_input]
            #print(command)
            process = subprocess.run(command)
            run_counter += 1
        

    def update_json(self):
        # Add TaskName field to BIDS functional NIFTI sidecars
        for func in self.func_name:
            with open(f'{self.func_path}/{func}.json') as json_file:
                data = json.load(json_file)
                data['TaskName'] = self.pdict["task"]

            with open(f'{self.func_path}/{func}.json', 'w') as outfile:
                json.dump(data,outfile)


    def run_fmriprep(self):
        # Run fmriprep-docker command
        pass


    def motionreg(self):
        # Run either GLM regression or ART repair for motion
        pass

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="command line parser")
    #parser.add_argument('-a', '--anat_input', required=True, help='Input the path to the anatomical DICOM')
    #parser.add_argument('-f', '--func_input', required=True, nargs='+', help='Input the paths to the functional DICOMs')
    #parser.add_argument('-r', '--root_dir', required=True, help='Input the path to the root of the BIDS directory you wish to create')
    parser.add_argument('-p', '--parameters', required=True, help='Input the paramters json')
    args = parser.parse_args()

    # Create and run FmriprepPipeline object
    pipeline = FmriprepPipeline()
    pipeline.read_json(args.parameters)
    pipeline.validate()
    pipeline.create_bids_hierarchy()
    pipeline.convert()
    pipeline.update_json()
    pipeline.run_fmriprep()
    pipeline.motionreg()
