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




## Runnning


```
python -m thor_magni_tools.run_header_check --dir_path=../datasets/thor_magni_zenodo/ --sc_id=Scenario_1
```