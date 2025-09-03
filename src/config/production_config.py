from abc import *
import argparse
import yaml

from utils.utils import get_relative_path



class BaseConfig(metaclass=ABCMeta):

    def __init__(self):
        parser = argparse.ArgumentParser(description='Arguments')

        default_config = "config/production_config.yaml"
        default_config = get_relative_path(default_config)

        default_models_config = "config/models.yaml" 
        default_models_config = get_relative_path(default_models_config)

        parser = argparse.ArgumentParser(description="Arguments")
        parser.add_argument(
            "--config", type=str, default=default_config, help="Path to environment config file"
        )
        parser.add_argument(
            "--local_models_config", type=str, default=default_models_config, help="Path to models path file"
        )

        parser.add_argument('--task', type=str, default='generation',
                            help='Specify processor number for multiprocessing')

        args = parser.parse_args()

        with open(args.local_models_config) as f:
            local_models_config = yaml.load(f, Loader=yaml.FullLoader)
            f.close()

        with open(args.config) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            f.close()


        self.config = {"runtime-config": vars(args), "yaml-config": config, "models-paths": local_models_config}