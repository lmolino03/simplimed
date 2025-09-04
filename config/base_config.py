from abc import *
import argparse
import yaml


class BaseConfig(metaclass=ABCMeta):

    def __init__(self):
        parser = argparse.ArgumentParser(description='Arguments')
        parser.add_argument('--config', type=str,
                            default='config/config.yaml',
                            help='A config path for env')
        parser.add_argument('--processor-num', type=int, default=4,
                            help='Specify processor number for multiprocessing')

        parser.add_argument("--log", default=False, action="store_true", help="Use log")
        parser.add_argument("--price", default=False, action="store_true", help="Calculate the price")

        parser.add_argument('--price_config', type=str,
                            default='config/price_config.yaml',
                            help='A config path for pricing')

        parser.add_argument("--preprocess", default=False, action="store_true", help="Preprocess the data and create "
                                                                                     "a new directory with processed "
                                                                                     "data")

        parser.add_argument('--task', type=str, default='generation',
                            help='Specify processor number for multiprocessing')

        args = parser.parse_args()

        with open(args.config) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            f.close()

        with open(args.price_config) as f:
            price_config = yaml.load(f, Loader=yaml.FullLoader)
            f.close()



        self.config = {"runtime-config": vars(args), "yaml-config": config, "price-config": price_config}


