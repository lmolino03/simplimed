import json
import os

from tqdm import tqdm

from utils.utils import convert_to_html, check_string_presence, load_json, get_model_response, get_prompts
from tasks.assemble import Base_Assembler


class seccionado(Base_Assembler):
    def __init__(self, args):
        super().__init__(args)

    def __generate_response(self, prompt, data, section, ingreso):
        if section == 'pruebas' or section == 'intervencion':
            content = data + "\n\n HOJA DE EVOLUCIÓN:\n\n"

            if self.price_flag:
                self.pricing.add(prompt, "input")
                self.pricing.add(prompt, "input")

            for j, reg in enumerate(self.ingresos[ingreso].informes['evolucion'].registros):
                if check_string_presence(reg, "pruebas complementarias"):
                    content += f"Registro {j + 1}:\n{reg}\n\n"
            return get_model_response(self.client, self.model, prompt, content, self.output_format)

        else:
            if self.price_flag:
                self.pricing.add(data, "input")
                self.pricing.add(prompt, "input")

            return get_model_response(self.client, self.model, prompt, data, self.output_format)

    def run(self):

        sections = ['motivo', 'antecedentes', 'enfermedad', 'pruebas', 'intervencion', 'juicio']
        recordatorio = self.reminder_sec

        prompts = get_prompts(recordatorio, self.output_format, _type="generate")

        ouput_second_path = f'generation_{self.results_name}_{self.model}'
        final_path = os.path.join(self.output_path, self.task, ouput_second_path)

        if self.output_format == 'JSON':
            altas_json_path = os.path.join(final_path, f'altas_json')

            if not os.path.exists(altas_json_path):
                os.makedirs(altas_json_path)

        altas_html_path = os.path.join(final_path, f'altas_html')

        if not os.path.exists(altas_html_path):
            os.makedirs(altas_html_path)

        prompt_path = os.path.join(final_path, f'prompt.txt')
        with open(prompt_path, 'w') as prompt_file:
            for pr in prompts:
                prompt_file.write(pr)
                prompt_file.write("\n")

        for ingreso in tqdm(self.ingresos):
            diccionarios = {}

            for i, zipp in enumerate(zip(prompts, sections)):
                prompt, section = zipp
                data = str(self.ingresos[ingreso].informes['anamnesis'])
                generado = self.__generate_response(prompt, data, section, ingreso)


                if self.price_flag:
                    self.pricing.add(generado, "output")

                if self.output_format == 'JSON':
                    diccionarios[section] = load_json(generado) if generado else None
                else:
                    diccionarios[section] = generado if generado else None


            args = {key: value for key, value in diccionarios.items() if value is not None}

            if self.output_format == 'JSON':
                with open(os.path.join(altas_json_path, f'alta_{ingreso}.json'), 'w') as json_file:
                    json.dump(args, json_file, indent=4)

            html_content = convert_to_html(args)

            with open(os.path.join(altas_html_path, f'alta_{ingreso}.html'), 'w') as html_file:
                html_file.write(html_content)

        if self.price_flag:
            self.pricing.get_log(final_path)
