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

* Trajectories preprocessing
  * [x] Interpolation given a max leap
  * [x] Downsampling given frequency
  * [x] Smoothing given a moving average window  

* Trajectories Analysis
  * [x] Tracking duration 
  * [x] Perception noise 
  * [x] Number of 8 sec tracklets
  * [x] Motion speed
  * [x] Path Efficiency
  * [ ] Minimal distance between people



## Running

### CSV headers checker

To check the alignment and consistency of headers in the csv files:

```
python -m thor_magni_tools.run_header_check --dir_path=PATH_TO_SCENARIO_FOLDER --sc_id=Scenario_1
```

### Preprocessing


To preprocess the data with interpolation, first one should set the parameters in the [cfg file](https://github.com/tmralmeida/thor-magni-tools/blob/main/thor_magni_tools/preprocessing/cfg.yaml) and then run:

```
python -m thor_magni_tools.run_preprocessing 
```

If [in_path](https://github.com/tmralmeida/thor-magni-tools/blob/main/thor_magni_tools/preprocessing/cfg.yaml#L1) is a folder, it will preprocess the files in the folder in parallel. 

### TODO 
Remove [this](https://github.com/tmralmeida/thor-magni-tools-new/blob/main/thor_magni_tools/utils/load.py#L28) when solved issue with duplicated frames


### Analysis

TODO: Table