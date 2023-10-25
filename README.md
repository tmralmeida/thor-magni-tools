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
  * [x] Interpolation give a max leap




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

If [in_path]([cfg file](https://github.com/tmralmeida/thor-magni-tools/blob/main/thor_magni_tools/preprocessing/cfg.yaml#L1) is a folder, it will preprocess the files in the folder in parallel. 