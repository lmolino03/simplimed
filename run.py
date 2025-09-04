from config.base_config import BaseConfig
from builder import Builder


def main():
    baseConfig = BaseConfig()
    Builder(baseConfig).build().run()


if __name__ == "__main__":
    main()
