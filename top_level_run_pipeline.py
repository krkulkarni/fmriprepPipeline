#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Feb 20, 2020

import bids_pythonic as bp

if __name__ == "__main__":
    
    singleecho_flag = True
    multiecho_flag = not singleecho_flag

    if singleecho_flag:
        fs_license = '/Applications/freesurfer/license.txt'
        project_dir = '/Volumes/synapse/home/kulkak01/fmriprepPipeline/'
        bids_root = f"{project_dir}/singleecho_rawdata/bids_root/"
        output_dir = f"{project_dir}/singleecho_rawdata/fmriprep_output/"
        dicom_dir = f"{project_dir}/singleecho_rawdata/dicoms/"
        subs = ['sub-01']

        bp.create_bids_root(bids_root)

        for s in subs:
            name = s
            anat = 'anat'
            func = [ 
                'session1',
                'session2'
            ]
            task = 'scriptreactivation'

            setup = bp.SetupBIDSPipeline(dicom_dir, name, anat, func, task, bids_root, ignore=True)
            setup.validate()
            setup.create_bids_hierarchy()
            setup.convert()
            setup.update_json()

        bp.run_fmriprep_docker(bids_root, output_dir, fs_license)


    elif multiecho_flag:
        fs_license = '/Applications/freesurfer/license.txt'
        project_dir = '/Volumes/synapse/home/kulkak01/fmriprepPipeline/'
        bids_root = f"{project_dir}/multiecho_rawdata/bids_root/"
        output_dir = f"{project_dir}/multiecho_rawdata/fmriprep_output/"
        dicom_dir = f"{project_dir}/multiecho_rawdata/dicoms/"
        subs = ['sub-02']

        # minerva_options = {
        #     'image_directory': f'{project_dir}',
        #     'batch_dir': f'{project_dir}/batch_dir',
        #     'hpc_home': '/hpc/home/kulkak01/',

        # }

        bp.create_bids_root(bids_root)

        for s in subs:
            name = s
            anat = 'anat'
            func = [ 
                [
                    'task-fish_run-1_echo-1',
                    'task-fish_run-1_echo-2'
                ]
            ]
            task = 'fish'

            setup = bp.SetupBIDSPipeline(dicom_dir, name, anat, func, task, bids_root, ignore=True, multiecho=True)
            setup.validate(multiecho=True)
            setup.create_bids_hierarchy()
            setup.convert(multiecho=True)
            setup.update_json()

    #fpsing = bp.FmriprepSingularityPipeline(subs, bids_root, output_dir, fs_license, freesurfer=False, minerva_options=minerva_options)
    #fpsing.create_singularity_batch()
    #fpsing.run_singularity_batch()
    #bp.motionreg(subs)