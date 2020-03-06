# fmriprepPipeline

A Python pipeline for BIDS creation and fmriprep.
From DICOM to BIDS directory structure creation, preprocessing with fmriprep, smoothing with AFNI, motion correction with ART Repair/GLM.

## Installation

Use conda to set up a new isolated environment to install requirements.
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install fmriprep-docker.
Use conda to install dcm2niix.

```bash
pip install --user --upgrade fmriprep-docker
conda install -c conda-forge dcm2niix
```

## Usage

```bash
python bids_scaffold.py -p parameters.json
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Authors

* **Kaustubh Kulkarni** - *Initial work* - [More Info](https://kulkarnik.com)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.
