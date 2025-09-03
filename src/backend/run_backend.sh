#!/bin/bash

echo "🟢 Iniciando procesamiento local en SIMPLIMED..."

# Moverse al directorio del proyecto
cd /home/lucas/SIMPLIMED/src/ || { echo "❌ Error: no se pudo acceder a /home/lucas/SIMPLIMED/src/"; exit 1; }

# Activar entorno Conda 'cardio'
eval "$(conda shell.bash hook)"
conda activate cardio || { echo "❌ Error: no se pudo activar el entorno conda 'cardio'"; exit 1; }

# Ejecutar el script Python con el argumento simplification
python -u production.py --task simplification || { echo "❌ Error al ejecutar production.py"; exit 1; }

echo "✅ Procesamiento completado correctamente."
