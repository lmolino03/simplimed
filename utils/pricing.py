import os

import tiktoken


class Pricing:
    def __init__(self, model, config):
        self.model = model

        self.encoding = tiktoken.encoding_for_model(model[:-1])

        self.input_price = config[self.model]["input"]
        self.output_price = config[self.model]["output"]


        self.input_total_tokens = 0
        self.output_total_tokens = 0

    def add(self, text, input_or_output):
        num_tokens = self.calculate_number_tokens(text)
        if input_or_output == "input":
            self.input_total_tokens += num_tokens
        elif input_or_output == "output":
            self.output_total_tokens += num_tokens

    def calculate_number_tokens(self, text):
        num_tokens = len(self.encoding.encode(text))
        return num_tokens

    def transform_name(self):
        options = ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002", "text-embedding-3-small",
                   "text-embedding-3-large"]
        for option in options:
            if self.model.startswith(option):
                return option
        return None

    def get_total_price(self):
        return (self.input_total_tokens / 1000000) * self.input_price + (self.output_total_tokens / 1000000) * self.output_price

    def get_log(self, path):
        price_path = os.path.join(path, f'price.txt')
        with open(price_path, 'w') as prompt_file:
            prompt_file.write(f'Model: {self.model}\n')
            prompt_file.write(f'Total price: {self.get_total_price()}\n')
            prompt_file.write(f'Total number of input tokens: {self.input_total_tokens}\n')
            prompt_file.write(f'Total number of output tokens: {self.output_total_tokens}\n')
            prompt_file.write(f'Price per 1M input tokens: {self.input_price}\n')
            prompt_file.write(f'Price per 1M output tokens: {self.output_price}\n')

