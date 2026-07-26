import json


class ConfigManager:

    def __init__(self, filename="config/config.json"):

        self.filename = filename

        self.data = {}

        self.load()


    def load(self):

        with open(self.filename, "r") as f:

            self.data = json.load(f)


    def save(self):

        with open(self.filename, "w") as f:

            json.dump(self.data, f, indent=4)


    def get(self, *keys):

        value = self.data

        for key in keys:

            value = value[key]

        return value


    def set(self, value, *keys):

        d = self.data

        for key in keys[:-1]:

            d = d[key]

        d[keys[-1]] = value

        self.save()

