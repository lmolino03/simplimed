import os

from openai import OpenAI
from tqdm import tqdm

from utils.utils import convert_to_html, check_string_presence
from tasks.assemble import Base_Assembler


class seccionado_string(Base_Assembler):
    def __init__(self, args):
        super().__init__(args)

    def run(self):
        client = OpenAI(api_key=self.api_key)

        if not os.path.exists('dataset/altas_json'):
            os.makedirs('dataset/altas_json')

        if not os.path.exists('dataset/altas_html'):
            os.makedirs('dataset/altas_html')

        for ingreso in tqdm(self.ingresos):

            motivo = self.ingresos[ingreso].informes['anamnesis'].secciones['motivo']
            txt = (f"Eres experto en generación de informes de alta hospitalaria. Se te proporcionarán la "
                   f"sección Motivo de Consulta de la hoja de anamnesis del paciente."
                   f"Deberás generar el apartado Motivo de Ingreso del informe de alta a partir de esta información.")
            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "text"},
                messages=[
                    {"role": "system", "content": txt},
                    {"role": "user", "content": motivo}
                ]
            )

            motivo_generado = response.choices[0].message.content

            antecedentes = str(self.ingresos[ingreso].informes['anamnesis'].secciones['antecedentes'])

            txt = (f"Eres experto en generación de informes de alta hospitalaria. Se te proporcionarán la "
                   f"sección Antecedentes de la hoja de anamnesis del paciente. "
                   f"Deberás generar el apartado Antecedentes del informe de alta a partir de esta información.")

            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "text"},
                messages=[
                    {"role": "system", "content": txt},
                    {"role": "user", "content": antecedentes}
                ]
            )

            antecedentes_generado = response.choices[0].message.content

            enfermedad = self.ingresos[ingreso].informes['anamnesis'].secciones['enfermedad']
            txt = (f"Eres experto en generación de informes de alta hospitalaria. Se te proporcionarán la "
                   f"sección Enfermedad Actual de la hoja de anamnesis del paciente."
                   f"Deberás generar el apartado Enfermedad Actual del informe de alta a partir de esta información.")

            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "text"},
                messages=[
                    {"role": "system", "content": txt},
                    {"role": "user", "content": enfermedad}
                ]
            )

            enfermedad_generado = response.choices[0].message.content

            pruebas_generado = None
            if self.ingresos[ingreso].informes['alta'].secciones['pruebas'] is not None:

                pruebas = str(self.ingresos[ingreso].informes['anamnesis']) + "\n\n HOJA DE EVOLUCIÓN:\n\n"

                for i, reg in enumerate(self.ingresos[ingreso].informes['evolucion'].registros):
                    if check_string_presence(reg, "pruebas complementarias"):
                        pruebas += f"Registro {i + 1}:\n{reg}\n\n"

                txt = (f"Eres experto en generación de informes de alta hospitalaria. Se te proporcionarán la "
                       f"la hoja de anamnesis junto con ciertos registro de la hoja de evolución del paciente."
                       f"Deberás generar el apartado Pruebas Complementarias del informe de alta a partir de esta información.")

                response = client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "text"},
                    messages=[
                        {"role": "system", "content": txt},
                        {"role": "user", "content": pruebas}
                    ]
                )

                pruebas_generado = response.choices[0].message.content

            intervencion_generado = None
            if self.ingresos[ingreso].informes['alta'].secciones['intervencion'] is not None:

                intervencion = str(self.ingresos[ingreso].informes['anamnesis']) + "\n\n HOJA DE EVOLUCIÓN:\n\n"

                for i, reg in enumerate(self.ingresos[ingreso].informes['evolucion'].registros):
                    if check_string_presence(reg, "pruebas complementarias"):
                        intervencion += f"Registro {i + 1}:\n{reg}\n\n"

                txt = (f"Eres experto en generación de informes de alta hospitalaria. Se te proporcionarán la "
                       f"la hoja de anamnesis junto con ciertos registro de la hoja de evolución del paciente."
                       f"Deberás generar el apartado Intervención Quirúrgica, que es distinto de las Pruebas Complementarias, del informe de alta a partir de esta información.")

                response = client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "text"},
                    messages=[
                        {"role": "system", "content": txt},
                        {"role": "user", "content": intervencion}
                    ]
                )

                intervencion_generado = response.choices[0].message.content

            juicio = str(self.ingresos[ingreso].informes['anamnesis'])
            reg_w_juicio = ''

            for i, reg in enumerate(self.ingresos[ingreso].informes['evolucion'].registros):
                if check_string_presence(reg, "juicio clínico"):
                    reg_w_juicio += f"Registro {i + 1}:\n{reg}\n\n"

            juicio += reg_w_juicio

            txt = (f"Eres experto en generación de informes de alta hospitalaria. Se te proporcionarán la "
                   f"sección la hoja de anamnesis del paciente unto con el último registro de la Hoja de Evolución.."
                   f"Deberás generar el apartado Juicio Clínico del informe de alta a partir de esta información.")

            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "text"},
                messages=[
                    {"role": "system", "content": txt},
                    {"role": "user", "content": juicio}
                ]
            )

            juicio_generado = response.choices[0].message.content

            args = {'Motivo de Ingreso': motivo_generado, 'Antecedentes': antecedentes_generado,
                    'Enfermedad Actual': enfermedad_generado, 'Pruebas Complementarias': pruebas_generado,
                    'Intervencion Quirúrgica': intervencion_generado, 'Juicio Clínico': juicio_generado}

            html_content = convert_to_html(args)

            with open(f'dataset/altas_html/alta_{ingreso}.html', 'w') as html_file:
                html_file.write(html_content)

            # print(response.choices[0].message.content)
            # 45, 73, 91, 77, 10, 16, 28, 85
