<h1 align="center">Welcome to RSTrace+ Replication Package 👋</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue.svg?cacheSeconds=2592000" />
</p>

> Run RSTrace+ with different configurations and datasets
## Prerequisities

- Python 3.8 and pip
- (Recommended) Virtual environment
- Neo4j 3.5.12

## Install dependencies

- `pip install -r requirements.txt`

## Configure

You can configure an experiment by modifying `config.yaml` file. Configuration fields:
- squareSum (boolean)
- recency (boolean)
- pathLenghtLimit (integer)
- dataset
  - type (string: "perceval" or "seoss" or "revrec")
  - commitsFilePath (string)
- method (string: "rstrace+" or "profile-based" or "revfinder")
- neo4j (object): Database configuration information
  - uri (string)
  - user (string)
  - password (string)

## Run
After configuration, run the experiment by:

`python src/ExperimentRunner.py`

When execution completed, results will be available under `results` directory and experiment logs will be under `logs` directory.

### Datasets from Perceval
- Qt 3D Studio
- Qt Creator

In `config.yaml` file, dataset type should be `perceval`.

### Datasets from SEOSS
- Apache Hive
- Apache Zookeeper

In `config.yaml` file, dataset type should be `seoss`.

### Datasets from RevRec

Datasets coming from https://github.com/XLipcak/rev-rec

In `config.yaml` file, dataset type should be `revrec`.

## Author

👤 **Emre Sülün**

* Website: [esulun.com](https://esulun.com)
* Github: [@sulunemre](https://github.com/sulunemre)


***
_This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator)_