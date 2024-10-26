import json
import os

_config_file = f"{os.path.realpath(os.path.dirname(__file__))}/config.json"


class Config:
    prefix = "!"
    invite_link = ""
    default_token_balance = 100000

    monitor = {
        "id": "0",
        "name": "test_name",
        "channel": "0",
    }

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_or_create_config()
        return cls._instance

    def _load_or_create_config(self):
        if os.path.exists(_config_file):
            with open(_config_file, "r") as f:
                stored_config = json.load(f)

            class_config = {
                k: v
                for k, v in self.__class__.__dict__.items()
                if not k.startswith("_") and not callable(v)
            }

            if class_config != stored_config:
                self._update_config(class_config)
        else:
            self._update_config()

    def _update_config(self, config=None):
        if config is None:
            config = {
                k: v
                for k, v in self.__class__.__dict__.items()
                if not k.startswith("_") and not callable(v)
            }

        with open(_config_file, "w") as f:
            json.dump(config, f, indent=4)

        for key, value in config.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self.__class__.__dict__[key]


config = Config()
