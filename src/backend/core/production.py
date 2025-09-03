import os
import threading
import time

from config.production_config import BaseConfig
from builder_production import Builder
from utils.utils import get_input_data, load_processed_files, save_processed_files

# Ruta al archivo de persistencia
processed_files_path = '/home/lucas/SIMPLIMED/src/processed_files.pkl'

# Lock global para acceso seguro
lock = threading.Lock()


def handle_launcher(file, baseConfig, processed_files, processed_files_path, lock):
    try:
        print(f"[HILO] Procesando archivo: {file}")
        with lock:
            processed_files[file] = "launched"
            save_processed_files(processed_files, processed_files_path)
        builder = Builder(baseConfig)
        launcher = builder.build(file)
        launcher.run()

        with lock:
            processed_files[file] = "executed"
            save_processed_files(processed_files, processed_files_path)
        print(f"[HILO] Archivo ejecutado correctamente: {file}")
    except Exception as e:
        print(f"[HILO] Error procesando archivo {file}: {e}")
        with lock:
            save_processed_files(processed_files, processed_files_path)


def monitor_directory(directory, builder, processed_files, processed_files_path, lock):
    while True:
        try:
            current_files = set(os.listdir(directory))
            with lock:
                already_processed = set(processed_files.keys())
            new_files = current_files - already_processed

            for file in new_files:
                full_path = os.path.join(directory, file)
                if os.path.isfile(full_path):
                    print(f"[MONITOR] Nuevo archivo detectado: {file}")
                    with lock:
                        processed_files[file] = "launched"
                        save_processed_files(processed_files, processed_files_path)

                    threading.Thread(
                        target=handle_launcher,
                        args=(file, builder, processed_files, processed_files_path, lock),
                        daemon=True
                    ).start()

                    with lock:
                        processed_files[file] = "launched"
                        save_processed_files(processed_files, processed_files_path)

            time.sleep(1)
        except Exception as e:
            print(f"[MONITOR] Error monitoreando el directorio: {e}")



def main():
    baseConfig = BaseConfig()
    production_data_path = get_input_data(baseConfig)

    processed_files = load_processed_files(processed_files_path)
    print(f"[MAIN] Archivos ya procesados: {processed_files}")

    monitor_thread = threading.Thread(
        target=monitor_directory,
        args=(production_data_path, baseConfig, processed_files, processed_files_path, lock),
        daemon=True
    )
    monitor_thread.start()

    # Mantener el hilo principal activo
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
