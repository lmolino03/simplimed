import json
import os
import re
import pdfplumber

from jinja2 import Template
from jinja2 import Environment, FileSystemLoader


def custom_isinstancedict(obj):
    # print(f"type:{type(obj)}")
    return isinstance(obj, dict)

def custom_isinstancelist(obj):
    # print(f"type:{type(obj)}")
    return isinstance(obj, list)

def read_pdf(pdf_file):
    texto = ''
    with pdfplumber.open(pdf_file) as pdf:
        for num_pagina in range(len(pdf.pages)):
            pagina = pdf.pages[num_pagina]

            texto_pag = pagina.extract_text()

            texto += texto_pag

    return texto


def get_tables(pdf_file):
    tables = []
    with pdfplumber.open(pdf_file) as pdf:
        for num_pagina in range(len(pdf.pages)):
            pagina = pdf.pages[num_pagina]

            tables_pag = pagina.extract_tables()
            tables.append(tables_pag)

    return tables


# Pág -> Anamnesis, Evolución, Alta
# NHC -> Anamnesis
# Jaén -> Evolución, Anamnesis
# http -> Alta
# fdo -> Alta
# Page -> Alta


def clean_text(text, substring):
    lines = text.split('\n')
    filtered_lines = [line for line in lines if substring not in line]
    txt = '\n'.join(filtered_lines)
    return txt


def remove_personal_data_anamnesis(text):
    return remove_personal_data(text, ["Motivo de Consulta"])


def remove_personal_data_evolucion(text):
    return remove_personal_data(text, ["Evolución"])


def remove_personal_data_alta(text):
    return remove_personal_data(text, ["Motivo de consulta", "Motivo de ingreso", "Antecedentes"])


def remove_personal_data(text, substrings):
    lines = text.split('\n')
    ini_index = None

    for i, line in enumerate(lines):
        if any(substring in line for substring in substrings):
            ini_index = i
            break
    if ini_index is not None:
        filtered_lines = lines[ini_index:]
        modified_text = '\n'.join(filtered_lines)
        return modified_text
    else:
        return text


def keep_text_before_keyword(text, substrings):
    lines = text.split('\n')
    end_index = None

    for i, line in enumerate(lines):
        if any(substring in line for substring in substrings):
            end_index = i
            break
    if end_index is not None:
        filtered_lines = lines[:end_index]
        modified_text = '\n'.join(filtered_lines)
        return modified_text
    else:
        return text


def remove_after_page(text):
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        if 'Page' in line:
            line = line.split('Page')[0]
        filtered_lines.append(line)
    modified_text = '\n'.join(filtered_lines)
    return modified_text


def get_key(text):
    pattern = r'\b\d+\b'
    key = re.findall(pattern, text)

    if key:
        return int(key[0])
    else:
        return None


def convert_to_html(json_data):
    # env = Environment(loader=FileSystemLoader('templates'))
    env = Environment(loader=FileSystemLoader('templates'))


    # env.globals['custom_isinstance'] = custom_isinstance

    data = json_data

    # print(data)

    if len(data) == 1:
        # Si el diccionario tiene exactamente una instancia
        _, data = next(iter(data.items()))

    # Cargar plantilla HTML desde un archivo o cadena
    with open('utils/template.html', 'r') as file:
        template_string = file.read()

    template = Template(template_string, )
    template.globals = {'isinstancelist': custom_isinstancelist, 'isinstancedict': custom_isinstancedict}
    # template.globals = {'isinstancedict': custom_isinstancedict}
    # template.globals = {'isinstancelist': custom_isinstancelist}


    # Renderizar el HTML utilizando los datos JSON
    html_content = template.render(data=data)
    return html_content


def flatten(lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list


def remove_none(lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.append(flatten(item))
        elif item is not None and item != '':
            flat_list.append(item)
    return flat_list


def check_string_presence(text, target_string):
    text_lower = text.lower()
    target_lower = target_string.lower()
    return target_lower in text_lower


def procesar_archivos(path, processor_class, container):
    archivos = os.listdir(path)
    for archivo in archivos:
        # print(archivo)
        ruta_completa = os.path.join(path, archivo)
        text = read_pdf(ruta_completa)
        args = (text, ruta_completa)
        processor = processor_class(args)
        processor.preprocess()
        args = processor.get_arguments()
        objeto = container(args)
        key = get_key(archivo)
        # print(objeto)
        yield key, objeto


def get_model_response(client, model, prompt, content, output_format):
    if output_format == 'JSON':
        out_format = "json_object"
    else:
        out_format = "text"

    response = client.chat.completions.create(
        model=model,
        response_format={"type": out_format},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )

    resp = response.choices[0].message.content

    # if resp[0:7] == "```json": resp = resp[8:-4]

    return resp


def load_json(data):
    return json.loads(data) if data else {}

def get_prompts(reminder, output_format, _type="generate"):
    if _type == "generate":
        return get_prompts_generate(reminder, output_format)
    elif _type == "simplify":
        return get_prompts_simplify(reminder, output_format)
    else: 
        raise NotImplementedError


def get_prompts_generate(reminder, output_format):
    apartados = ["Motivo de Ingreso", "Antecedentes", "Enfermedad Actual", "Pruebas Complementarias",
                 "Intervención Quirúrgica, que es distinto de las Pruebas Complementarias,", "Juicio Clínico"]
    datos_proporcionados = ["Se te proporcionarán la sección Motivo de Consulta de la hoja de anamnesis del paciente.",
                            "Se te proporcionarán la sección Antecedentes de la hoja de anamnesis del paciente.",
                            "Se te proporcionarán la sección Enfermedad Actual de la hoja de anamnesis del paciente.",
                            "Se te proporcionarán la hoja de anamnesis junto con ciertos registros de la hoja de evolución del paciente.",
                            "Se te proporcionarán la hoja de anamnesis junto con ciertos registros de la hoja de evolución del paciente.",
                            "Se te proporcionarán la sección la hoja de anamnesis del paciente junto con el último registro de la Hoja de Evolución."]

    prompts = []
    inicio = "Eres experto en generación de informes de alta hospitalaria."
    final_ini = "Deberás generar el apartado"

    if output_format == 'JSON':
        final_fin = "del informe de alta a partir de esta información en formato JSON."

        for i in range(0, 6):
            prompt = f'{inicio} {datos_proporcionados[i]} {final_ini} {apartados[i]} {final_fin} {reminder}'
            prompts.append(prompt)

    elif output_format == 'string':
        final_fin = "del informe de alta a partir de esta información."

        for i in range(0, 6):
            prompt = f'{inicio} {datos_proporcionados[i]} {final_ini} {apartados} {final_fin}'
            prompts.append(prompt)

    return prompts

def get_prompts_simplify(reminder, output_format):
    apartados = ["Motivo de Ingreso", "Antecedentes", "Enfermedad Actual", "Pruebas Complementarias",
                 "Evolución y Curso Clínico", "Intervención Quirúrgica", "Pruebas Complementarias", "Juicio Clínico", "Plan de Actuación", "Tratamiento", "Revisiones"]
    
    prompts = []

    for ap in apartados:

        if output_format == 'JSON':
            prompt_inicial = (f'Eres especialista en simplifación de informes de alta de cardiología. Tu tarea es simplificar la sección {ap}'
                        f' para hacerlo más fáciles de entender para personas mayores. Por favor, proporciona una respuesta clara y concisa que'
                        f' conserve el significado original de cada oración, eliminando cualquier complejidad o jerga innecesaria, además, deberás'
                        f' explicar la terminología médica, especialmente la relacionada con cardiologia. Ten en cuenta que tu respuesta debe ser'
                        f' lo suficientemente flexible como para permitir varias simplificaciones relevantes y creativas, siempre y cuando transmitan'
                        f' con precisión el significado previsto. \n\n Por favor, simplifica la sección {ap} del informe de alta y devuelve los datos en formato JSON:')

            prompts.append(prompt_inicial)

        else:
            prompt_inicial = (f'Eres especialista en simplifación de informes de alta de cardiología. Tu tarea es simplificar la sección {ap}'
                                    f' para hacerlo más fáciles de entender para personas mayores. Por favor, proporciona una respuesta clara y concisa que'
                                    f' conserve el significado original de cada oración, eliminando cualquier complejidad o jerga innecesaria, además, deberás'
                                    f' explicar la terminología médica, especialmente la relacionada con cardiologia. Ten en cuenta que tu respuesta debe ser'
                                    f' lo suficientemente flexible como para permitir varias simplificaciones relevantes y creativas, siempre y cuando transmitan'
                                    f' con precisión el significado previsto. \n\n Por favor, simplifica la sección {ap} del informe de alta:')

            prompts.append(prompt_inicial)


    return prompts
