// Obtener referencias a los elementos del DOM
const fileInput = document.getElementById("file-input");
const pdfPreview = document.getElementById("pdf-preview");
const statusMessage = document.getElementById("status-message");

// Manejar la selección del archivo
fileInput.addEventListener("change", () => {
    const uploadedFile = fileInput.files[0];

    if (uploadedFile) {
        // Verificar que sea un archivo PDF
        if (uploadedFile.type !== "application/pdf") {
            alert("Por favor, selecciona un archivo PDF válido.");
            return;
        }

        // Crear una URL para el archivo y mostrarlo en el visor
        const fileURL = URL.createObjectURL(uploadedFile);
        pdfPreview.src = fileURL;
    }
});
