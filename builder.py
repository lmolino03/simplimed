import os
import pickle
import warnings
import importlib.util

from tqdm import tqdm

# from assembly.GPT.completo import GPT_GenInformeCompleto
# from assembly.GPT.seccionado import GPT_GenInformeSeccionado
# from assembly.GPT.seccionado_string import GPT_GenInformeSeccionadoString

from data_structures.Anamnesis import HojaAnamnesis
from data_structures.Hoja_Evolucion import HojaEvolucion
from data_structures.Informe_Alta import InformeAlta
from data_structures.Ingreso import Ingreso

from preprocess.processor_alta import ProcessorAlta
from preprocess.processor_anamnesis import ProcessorAnamnesis
from preprocess.processor_evol import ProcessorEvolucion

from utils.utils import procesar_archivos


class Builder:
    def __init__(self, baseconfig):
        self.config = baseconfig

    def build(self):
        evol_path = self.config.config['yaml-config']['paths']['input']['evol']
        alta_path = self.config.config['yaml-config']['paths']['input']['alta']
        anamnesis_path = self.config.config['yaml-config']['paths']['input']['anamnesis']
        preprocessed_path = self.config.config['yaml-config']['paths']['output']['preprocessed_ingresos']

        # log = self.config.config['runtime-config']['log']
        preprocess = self.config.config['runtime-config']['preprocess']

        hojas_evol = {}
        hojas_anamnesis = {}
        informes_alta = {}
        ingresos = {}
        ingresos_aptos = {}

        if preprocess:
            if os.path.exists(preprocessed_path):
                warnings.warn("El directorio de ingresos ya existe. Se pueden sobrescribir archivos existentes.",
                              UserWarning)

            print("Preprocesando hojas de evolución...")
            for key, object in tqdm(procesar_archivos(evol_path, ProcessorEvolucion, HojaEvolucion),
                                    total=75):
                hojas_evol[key] = object

            print("Preprocesando hojas de anamnesis...")
            for key, object in tqdm(procesar_archivos(anamnesis_path, ProcessorAnamnesis, HojaAnamnesis), total=71):
                hojas_anamnesis[key] = object

            print("Preprocesando informes de alta...")
            for key, object in tqdm(procesar_archivos(alta_path, ProcessorAlta, InformeAlta), total=100):
                informes_alta[key] = object

            if not os.path.exists(preprocessed_path):
                os.makedirs(preprocessed_path)

            for i in range(100):
                anamnesis = None
                evolucion = None

                n = i + 1
                if n in hojas_anamnesis:
                    anamnesis = hojas_anamnesis[n]
                if n in hojas_evol:
                    evolucion = hojas_evol[n]
                alta = informes_alta[n]

                args = (anamnesis, evolucion, alta)
                ingreso = Ingreso(args)
                ingresos[i] = ingreso

                if ingreso.es_apto():
                    ingresos_aptos[n] = ingreso
                    new_filepath = os.path.join(preprocessed_path, f"ingreso_{n}.pickle")
                    with open(new_filepath, "wb") as file:
                        pickle.dump(ingreso, file)

        for filename in os.listdir(preprocessed_path):
            if filename.endswith(".pickle"):
                filepath = os.path.join(preprocessed_path, filename)
                with open(filepath, "rb") as file:
                    ingreso = pickle.load(file)

                numero_ingreso = int(filename.split("_")[1].split(".")[0])
                ingresos_aptos[numero_ingreso] = ingreso

        return self.createAssemble(ingresos_aptos)

    def createAssemble(self, ingresos):
        output_path = self.config.config['yaml-config']['paths']['output']['output_data']
        results_name = self.config.config['yaml-config']['paths']['output']['results_name']
        price = self.config.config['runtime-config']['price']
        task = self.config.config['runtime-config']['task']


        name = self.config.config['yaml-config']['model']['name']
        if name == 'GPT':
            key = self.config.config['yaml-config']['model']['api_key']
            policy = self.config.config['yaml-config']['model']['policy']
            type = self.config.config['yaml-config']['model']['type']
            output_format = self.config.config['yaml-config']['model']['output_format']

            price_config = None
            if price:
                price_config = self.config.config['price-config']

            args = (ingresos, key, type, output_format, output_path, results_name, price, price_config, name, task)

            mod = f'tasks/{task}/'
            mod += f'{name}/'

            spec = importlib.util.spec_from_file_location("my_module", mod + policy + '.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            _class = getattr(module, policy)
            model = _class(args)

        else:
            raise (NotImplementedError)

        return model
