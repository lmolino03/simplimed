import os
import logging
import json

from tqdm import tqdm
from tasks.assemble import BaseAssembler
from nltk.tokenize import sent_tokenize

from utils.utils import get_model_response_llm, get_prompts, convert_section_to_markdown

class seccionado(BaseAssembler):
    """Class for processing and generating reports based on sections of medical data."""
    
    def __init__(self, args):
        """
        Initializes the Seccionado class with configuration arguments.
        
        Args:
            args (Namespace): Configuration settings passed as arguments.
        """
        super().__init__(args)
        self.logger = logging.getLogger(__name__)

    def run(self):
        """
        Runs the process of generating reports, handling each section of the medical data.
        """

        self.logger.info("Starting the report generation process.")

        # Get the prompts for the sections based on the configuration
        prompts = get_prompts(self.output_format, self.task, self.model_name, self.policy)        

        output_file = os.path.join(self.output_path, self.output_file)

        with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"\n# Informe de Alta Simplificado generado por IA\n\n")

        # Iterate through each "ingreso" (admission)
        for ingreso in self.ingresos:

            diccionarios = {}
            
            # Retrieve available section keys
            keys_apartados = self.ingresos[ingreso].informes['alta'].secciones.keys()

            self.logger.info(f"Working on ingreso {ingreso}")

            # Process each section
            for section_key in keys_apartados:

                data = self.ingresos[ingreso].informes['alta'][section_key]

                if not section_key or not data: 
                    self.logger.warning(f"Skipping section {section_key} for ingreso {ingreso} due to missing data or invalid section.")
                    continue  # Skip if the section is not mapped or not data
 
                prompt = prompts.get(section_key, None)
                abreviaciones = set()

                data_copy = data
                
                if True:
                    frases = sent_tokenize(data, language="spanish")
                    for frase in frases:
                        abreviaciones.update(self.extractor_abreviaciones.extraer_abreviaciones(self.client, frase))

                    prompt += "\nAquí tienes lo que puede significar cada abreviación presente en el texto, en caso de que pueda signficar más de una abreviación, elige la que más probable sea:"

                    for abreviacion in abreviaciones:
                        if abreviacion.isupper():
                            sig = self.buscador_abreviaciones.buscar_abreviacion(abreviacion)
                            if isinstance(sig, str):
                                prompt += f"\n{abreviacion}: "
                                prompt += sig
                                data_copy = data_copy.replace(abreviacion, sig)

                            elif isinstance(sig, list):
                                sig_rep = sig[0].replace(".", "")
                                for s in sig:
                                    prompt += f"\n{abreviacion}: "
                                    prompt += s

                                    if len(s.strip().split()) == 1:
                                        print(s.strip().split())
                                        sig_rep = s

                                data_copy = data_copy.replace(abreviacion, sig_rep.replace(".", ""))
                
                if section_key == "tratamiento" and True:
                    data_copy = data_copy.replace('**', '')
                    # print(data_copy)
                    if "RECOMENDACIONES SOBRE LA DIETA" in data_copy: data_copy = data_copy.lower().split("RECOMENDACIONES SOBRE LA DIETA")[0].strip()
                    frases_copy = sent_tokenize(data_copy, language="spanish")
                    elementos = [parte.strip() for frase in frases_copy for parte in frase.split("\n") if parte.strip()]
                    elementos = [parte.strip() for frase in elementos for parte in frase.split(",") if parte.strip()]

                    prompt += "\n\nAquí tienes el uso terapéutico de los medicamentos/principios activos presentes en el texto:"

                    # print(data)
                    for frase in elementos:
                        medicamentos = self.extractor_medicamento.extraer_medicamentos(self.client, frase)
                        significado = None
                        if not medicamentos:
                            medicamentos = [frase.split()[0]]
                        
                        if medicamentos: 
                            significado = self.buscador_medicamentos.mejor_coincidencia(medicamentos)

                        if significado:
                            prompt += f"\n{significado["nombre_LLM"]}. Principios activos ({significado["principiosActivos"]}): {significado["uso_terapeutico"]}"

                # Generate the response based on the prompt and data
                self.logger.info(f"Generating response for section {section_key} in ingreso {ingreso}.")
                generated_response = self.__generate_response(prompt, data, convert_section_to_markdown(section_key))
                # print(generated_response)

                if not generated_response:
                    self.logger.warning(f"Failed to generate response for section {section_key} in ingreso {ingreso}.")

                
            

           

    def __generate_response(self, prompt, data, section_key):
        """
        Generates a response from the GPT model based on the provided prompt and data.

        Args:
            prompt (str): The prompt for the model.
            data (str): The data to generate a response for.

        Returns:
            str: The generated response.
        """

        output_file = os.path.join(self.output_path, self.output_file)
        

        # Call the function to get the model's response
        return get_model_response_llm(self.client, prompt, data, self.model_path, section_key, output_file)
        # return get_model_response_llm(self.model, self.tokenizer, prompt, data, self.model_name, section_key, output_file)
