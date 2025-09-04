from openai import OpenAI
from abc import ABC, abstractmethod

from utils.pricing import Pricing


class Base_Assembler(ABC):
    def __init__(self, args):
        self.ingresos, self.api_key, self.model, self.output_format, self.output_path, self.results_name, self.price_flag, self.price_config, self.name, self.task = args

        if self.name == 'GPT':
            self.client = OpenAI(api_key=self.api_key)
        else:
            raise(NotImplementedError)

        self.reminder_comp = "El JSON tiene que incluir solo estos campos, sin ninguna información adicional."
        self.reminder_sec = "El JSON tiene que incluir solo este campo, sin ninguna información adicional y sin nigún campo más."

        if self.price_flag:
            self.pricing = Pricing(self.model, self.price_config)

    @abstractmethod
    def run(self):
        pass
