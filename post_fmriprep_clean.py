#!/usr/bin/env python
# Author: Kaustubh Kulkarni
# Date: Dec 12, 2020

"""

Use this module to clean BIDS-formatted fmriprep output directory after
running fmriprepPipeline

Functions performed:
1. Mask image with fmriprep-generated brain mask
2. Smooth preprocessed image
3. Nuisance regression with chosen confounds

"""

from nilearn.input_data import NiftiMasker
from nilearn.image import load_img, resample_img
from nilearn.masking import apply_mask, unmask
import numpy as np
import sys, os
import glob


# Check for correct versioning
if sys.version_info[0] < 3:
	raise Exception("Must be using Python 3")

class PostFmriprep(object):
	""" 
	Setup instance with class methods to post-process BIDS formatted directory structure.

	"""
	def __init__(self, root, runs, tasks, output_dir):
		self.pdict = {}
		self.pdict['root'] = root
		self.pdict['output_dir'] = output_dir
		self.pdict['masked_dir'] = None
		self.pdict['nuisance_reg_dir'] = None
		
		self.pdict['subjects'] = []
		for entry in os.listdir(root):
			if os.path.isdir(os.path.join(root, entry)) and entry.startswith('sub'):
				self.pdict['subjects'].append(entry)

		self.pdict['runs'] = np.arange(runs)+1
		self.pdict['tasks'] = tasks


	def get_subjects(self):
		return self.pdict['subjects']
	def get_runs(self):
		return self.pdict['runs']

	def mask_subjects(self, subs=None, runs=None, tasks=None, smoothing=None):
		""" 
		Mask the subjects with their fmriprep outputted brain mask and smooth.
	  
		Parameters: 
		subs (str arr): list of all subjects
		runs (int): number of runs
		smoothing (int): FWHM of smoothing kernel 

		"""

		mask_output = os.path.join(self.pdict['output_dir'], 'masked')
		if not os.path.exists(mask_output):
			os.makedirs(mask_output)
		self.pdict['masked_dir'] = mask_output

		if not subs:
			subs = self.pdict['subjects']
		if not runs:
			runs = self.pdict['runs']
		if not tasks:
			tasks = self.pdict['tasks']

		for sub in subs:
			sub_path = os.path.join(mask_output, sub)
			if not os.path.exists(sub_path):
				os.makedirs(sub_path)
			self.pdict['masked_dir'] = mask_output

			for task in tasks:
				for run in runs:
					print(f'Working on {sub}, task:{task}, run:{run}')
					mask_pattern = f'*task-{task}*run-{run}*brain_mask*nii.gz'
					nifti_pattern = f'*task-{task}*run-{run}*preproc_bold*nii*'
					mask = glob.glob(os.path.join(self.pdict['root'], sub, 'func', mask_pattern))[0]
					nifti = glob.glob(os.path.join(self.pdict['root'], sub, 'func', nifti_pattern))[0]
					# mask_img = load_img(mask)
					# nifti_img = load_img(nifti)
				
					masker = NiftiMasker(mask_img=mask, smoothing_fwhm=smoothing, verbose=5)
					masked_data = masker.fit_transform(nifti)
					print('Transforming data back into nifti and saving')
					masked_img = masker.inverse_transform(masked_data)

					mask_img_name = f'{sub}_run-{run}_preproc_bold_mask_smooth.nii.gz'
					masked_img.to_filename(os.path.join(sub_path, mask_img_name))

	def nuisance_regression(self, confounds, subs=None, runs=None):
		""" 
		Regress chosen confounds from masked
	  
		Parameters: 
		subs (str arr): list of all subjects
		runs (int): number of runs
		smoothing (int): FWHM of smoothing kernel 

		"""

		nr_output = os.path.join(self.pdict['output_dir'], 'nuisance_regression')
		if not os.path.exists(nr_output):
			os.makedirs(nr_output)
		self.pdict['nuisance_reg_dir'] = nr_output

		if not self.pdict['masked_dir']:
			raise OSError('Masked directory does not exist. Run mask_subjects function first!')

		if not subs:
			subs = self.pdict['subjects']
		if not runs:
			runs = self.pdict['runs']

		for sub in subs:
			for run in runs:

				input_img_name = os.path.join(self.pdict['masked_dir'], f'{sub}_run-{run}_preproc_bold_mask_smooth.nii.gz')
				masked_img.to_filename(os.path.join(mask_output, mask_img_name))





























				


