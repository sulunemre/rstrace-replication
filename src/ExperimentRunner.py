"""Run an experiment with the configuration in config.yaml
"""

from Experiment import Experiment
import yaml

if __name__ ==  '__main__':
    with open("config.yaml", "r") as stream:
        config = None
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exception:
            print(exception)

    experiment = Experiment(config)
    experiment.run()
