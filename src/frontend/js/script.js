function handleFileUpload(input) {
    const file = input.files[0];
    if (file && file.type === 'application/pdf') {
        uploadFile(file);
    } else {
        alert('Por favor, sube un archivo PDF');
    }
}

function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        uploadFile(file);
    } else {
        document.getElementById('status-message').textContent = 'Por favor, sube un archivo PDF válido.';
    }
}

function uploadFile(file) {
    document.getElementById('loading-message').style.display = 'block';
    document.getElementById('status-message').textContent = 'Subiendo el archivo...';

    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loading-message').style.display = 'none';

        if (data.fileName) {
            document.getElementById('status-message').textContent = 'Archivo subido exitosamente.';
            window.location.href = `/preview?fileName=${data.fileName}`;
        } else {
            document.getElementById('status-message').textContent = 'Error al subir el archivo.';
        }
    })
    .catch(error => {
        console.error('Error en la subida del archivo:', error);
        document.getElementById('loading-message').style.display = 'none';
        document.getElementById('status-message').textContent = 'Hubo un problema al procesar el archivo. Inténtalo de nuevo.';
    });
}

// Prevenir comportamiento por defecto
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.querySelector('.upload-area').addEventListener(eventName, e => e.preventDefault());
});

document.querySelector('.upload-area').addEventListener('drop', handleDrop);


// Procesar el archivo y redirigir
function processFile(file) {
    if (file.type !== 'application/pdf') {
        document.getElementById('status-message').textContent = 'Por favor, sube un archivo PDF válido.';
        return;
    }

    // Mostrar mensaje de carga
    document.getElementById('loading-message').style.display = 'block';

    // Crear un FormData para enviar al servidor
    const formData = new FormData();
    formData.append('file', file);

    // Enviar al servidor
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            // Redirigir a la página de previsualización
            window.location.href = '/preview';
        } else {
            throw new Error('Error al subir el archivo');
        }
    })
    .catch(error => {
        document.getElementById('loading-message').style.display = 'none';
        document.getElementById('status-message').textContent = 'Hubo un problema al procesar el archivo. Inténtalo de nuevo.';
    });
}

// Agregar listeners para arrastrar y soltar
document.querySelector('.upload-area').addEventListener('dragover', event => event.preventDefault());
document.querySelector('.upload-area').addEventListener('drop', handleDrop);
