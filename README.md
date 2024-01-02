# thor-magni-tools
Preprocessing and filtering tools for THÖR-Magni human motion dataset.


# Install

Install [miniconda](http://docs.conda.io/en/latest/miniconda.html). Then, you can install all packages required by running:

```
conda env create -f ex_environment.yml && conda activate thor-magni-tools
```


## Current status

* CSV validation
  * [x] Header checker
  * [x] Header/dataframe alignment

* THÖR/THÖR-Magni trackings filtering:
  * [x] Best marker
  * [x] Tracking restoring 


* Trajectories preprocessing
  * [x] Interpolation given a max leap
  * [x] Downsampling given frequency
  * [x] Smoothing given a moving average window  

* Trajectories Analysis
  * [x] Tracking duration 
  * [x] Number of 8 sec tracklets
  * [x] Motion speed
  * [x] Path Efficiency
  * [x] Minimal distance between people

* Dataset Comparison
  * [x] THÖR
  * [x] ETH/UCY
  * [x] SDD
  * [x] ATC


## Running

### Download the dataset

First, the most important step is to download the dataset from [zenodo](10.5281/zenodo.10407222).
Run:

```
curl -O https://zenodo.org/records/10407223/files/THOR_MAGNI.zip\?download\=1 && unzip -r THOR_MAGNI.zip && rm -rf THOR_MAGNI.zip
```

The CSV files for each Scenario can be found in `THOR_MAGNI\CSVs_Scenarios`.


### CSV headers checker

To check the alignment and consistency of headers in the csv files:

```
python -m thor_magni_tools.run_header_check --dir_path=PATH_TO_SCENARIO_FOLDER --sc_id=Scenario_1
```

### Preprocessing


To preprocess the data with interpolation (and optional downsampling and moving average filter), first one should set the parameters in the [cfg file](https://github.com/tmralmeida/thor-magni-tools/blob/main/thor_magni_tools/preprocessing/cfg.yaml) and then run:

```
python -m thor_magni_tools.run_preprocessing 
```

If [in_path](https://github.com/tmralmeida/thor-magni-tools/blob/main/thor_magni_tools/preprocessing/cfg.yaml#L1) is a folder, it will preprocess the files in the folder in parallel. 
After finishing, the files will be stored in the [pre-specified output path](https://github.com/tmralmeida/thor-magni-tools/blob/main/thor_magni_tools/preprocessing/cfg.yaml#L2) with the 
format | time | frame_id | x | y | z | ag_id | data_label, where `ag_id` is the helmet number and `data_label` is the role of the participant.


### Analysis

```
python -m thor_magni_tools.run_analysis --data_path=DATASET_FOLDER OR DATASET FILE --dataset DATASET_NAME 
```

Such that `DATASET_NAME` in {"thor_magni", "thor", "eth_ucy", "sdd", "atc"}.

Optional Arguments:

| Parameter                 | Default       | Description   |	
| :------------------------ |:-------------:| :-------------|
| `--interpolation` 	        |	None          |used to preprocess the dataset. Max frames without tracking |
| `--average_window` 	        |	None          |used to preprocess the dataset. Number of periods to average |
| `--filtering_markers` 	    |	3D-restoration          |filtering markers type used in THÖR/THÖR-Magni tracks |
