import json
import os

from tqdm import tqdm

from utils.utils import convert_to_html, get_model_response
from tasks.assemble import Base_Assembler


class completo(Base_Assembler):
    def __init__(self, args):
        super().__init__(args)

        self.texto_inicial = (f"Eres experto en generación de informes de alta hospitalaria. Se te proporcionarán la "
                              f"hoja de evolución y la hoja de anamnesis del paciente. Crea un informe de alta en "
                              f"formato JSON con los siguientes apartados:")

    def run(self):

        ouput_second_path = f'generation_{self.results_name}_{self.model}'
        final_path = os.path.join(self.output_path, self.task, ouput_second_path)

        altas_json_path = os.path.join(final_path, 'altas_json')

        if not os.path.exists(altas_json_path):
            os.makedirs(altas_json_path)

        altas_html_path = os.path.join(final_path, 'altas_html')

        if not os.path.exists(altas_html_path):
            os.makedirs(altas_html_path)


        apartados = self.ingresos[list(self.ingresos.keys())[0]].get_apartados()
        prompt = self.texto_inicial + apartados + ". " + self.reminder_comp

        prompt_path = os.path.join(final_path, f'prompt.txt')
        with open(prompt_path, 'w') as prompt_file:
            prompt_file.write(prompt)

        for ingreso in tqdm(self.ingresos):
            # print(ingreso)

            apartados = self.ingresos[ingreso].get_apartados()
            prompt = self.texto_inicial + apartados + self.reminder_comp
            content = self.ingresos[ingreso].getInput()
            resp = get_model_response(self.client, self.model, prompt, content,
                                      self.output_format)

            if self.price_flag:
                self.pricing.add(prompt, "input")
                self.pricing.add(content, "input")
                self.pricing.add(resp, "output")


            json_file_join = os.path.join(altas_json_path, f'alta_{ingreso}.json')
            html_file_join = os.path.join(altas_html_path, f'alta_{ingreso}.html')

            try:
                data = json.loads(resp)
                with open(json_file_join, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                html_content = convert_to_html(data)
                with open(html_file_join, 'w') as html_file:
                    html_file.write(html_content)
            except json.JSONDecodeError as e:
                error_message = f"Error decoding JSON for ingreso {ingreso}: {e}"
                print(error_message)

        if self.price_flag:
            self.pricing.get_log(final_path)

