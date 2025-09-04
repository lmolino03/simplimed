import json
import os

from tqdm import tqdm

from utils.utils import convert_to_html, get_model_response
from tasks.assemble import Base_Assembler


class completo(Base_Assembler):
    def __init__(self, args):
        super().__init__(args)

        self.texto_inicial = (f"Eres especialista en simplifacion de informes de alta de cardiologia. Tu tarea es simplificar el siguiente informe para hacerlo más fáciles de entender para personas mayores. Por favor, proporciona una respuesta clara y concisa que conserve el significado original de cada oración, eliminando cualquier complejidad o jerga innecesaria, además, deberás explicar la terminología médica, especialmente la relacionada con cardiologia. Ten en cuenta que tu respuesta debe ser lo suficientemente flexible como para permitir varias simplificaciones relevantes y creativas, siempre y cuando transmitan con precisión el significado previsto. El informe de alta tiene los siguientes apartados: ")
        self.texto_final = (f"\nPor favor, simplifica este informe de alta y devuelve la simplificacion en formato JSON:")

    def run(self):

        ouput_second_path = f'simplification_{self.results_name}_{self.model}'
        final_path = os.path.join(self.output_path, self.task, ouput_second_path)

        altas_json_path = os.path.join(final_path, 'simplificacion_json')

        if not os.path.exists(altas_json_path):
            os.makedirs(altas_json_path)

        altas_html_path = os.path.join(final_path, 'simplificacion_html')

        if not os.path.exists(altas_html_path):
            os.makedirs(altas_html_path)


        apartados = self.ingresos[list(self.ingresos.keys())[0]].get_apartados()
        prompt = self.texto_inicial + apartados + self.texto_final


        prompt_path = os.path.join(final_path, f'prompt.txt')
        with open(prompt_path, 'w') as prompt_file:
            prompt_file.write(prompt)


        for ingreso in tqdm(self.ingresos):
            # print(ingreso)

            apartados = self.ingresos[ingreso].get_apartados()
            prompt = self.texto_inicial + apartados + self.texto_final
            content = self.ingresos[ingreso].getOutput()
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

