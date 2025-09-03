document.addEventListener("DOMContentLoaded", () => {
    const pdfCanvasContainer = document.getElementById("pdf-canvas-container");
    const outputContainer = document.getElementById("output-container");
    const outputContent = document.getElementById("output-content");
    const generateBtn = document.getElementById("generate-btn");
    const uploadedPdfPath = new URLSearchParams(window.location.search).get('fileName');

    const eventSource = new EventSource(`/events?clientId=${encodeURIComponent(uploadedPdfPath)}`);

    // Variable para almacenar los chunks recibidos
    let accumulatedChunks = "";
    let displayedChars = 0;
    let firstChunkReceived = false;

    // Escuchar los mensajes del servidor
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'fileChunk') {
            if (!firstChunkReceived) {
                document.getElementById('loading-indicator').style.display = "none";
                document.getElementById('loading-message').style.display = "none";
                firstChunkReceived = true;
            }

            // Acumulamos los chunks
            accumulatedChunks += data.chunk;

            // Procesar el contenido cada vez que lleguen nuevos datos
            const cleanedContent = accumulatedChunks.replace(/\n{2,}/g, "\n").trim();
            
            // Mostrar letra por letra usando un intervalo
            displayContentLetterByLetter(cleanedContent);
        }
    };

    // Función para mostrar el contenido letra por letra
    function displayContentLetterByLetter(content) {
        // Si ya hemos mostrado todo el contenido actual, no hacemos nada
        if (displayedChars >= content.length) return;
        
        // Calculamos cuántas letras nuevas tenemos que mostrar
        const interval = setInterval(() => {
            // Tomamos el contenido hasta la letra actual
            const partialContent = content.substring(0, displayedChars + 1);
            
            // Mostrar el contenido parcial
            displayContent(partialContent);
            
            // Incrementar el contador de caracteres mostrados
            displayedChars++;
            
            // Si ya mostramos todo el contenido disponible, detener el intervalo
            if (displayedChars >= content.length) {
                clearInterval(interval);
            }
        }, 20); // Velocidad de escritura: 20ms por letra (ajustable)
    }

    // Mostrar el contenido procesado
    function displayContent(content) {
        // Convertir a HTML (si es necesario)
        outputContent.innerHTML = markdown.toHTML(content);
        
        // Aplicar estilos directamente sin transición
        const markdownElements = outputContent.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li');
        markdownElements.forEach((element) => {
            element.classList.add('markdown-text');
            element.style.color = '#333'; // Aplicar el color directamente
        });
    }
        

    // Manejo de errores de la conexión SSE
    eventSource.onerror = (error) => {
        console.error('Error en la conexión SSE:', error);
        alert('Hubo un problema con la conexión al servidor.');
    };
    
    



    if (uploadedPdfPath) {
        const url = uploadedPdfPath;
        console.log('Página de vista previa cargada para el archivo:', uploadedPdfPath);
        
        // Detectar cuando el usuario intente abandonar la página
        window.addEventListener("beforeunload", (e) => {
            console.log('El cliente está abandonando la página de vista previa.');

            // Enviar una notificación al servidor para eliminar el archivo
            fetch('/notifyPreviewExit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fileName: uploadedPdfPath })
            })
            .then(response => response.json())
            .catch(error => console.error('Error al notificar al servidor:', error));
        });
    }
    
    
    // Renderizar el PDF si se ha subido
    if (uploadedPdfPath) {
        const url = '/tempUploads/' + uploadedPdfPath;

        pdfjsLib.getDocument(url).promise.then((pdfDoc_) => {
            const pdfDoc = pdfDoc_;
            const totalPages = pdfDoc.numPages;

            for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
                pdfDoc.getPage(pageNum).then((page) => {
                    const viewport = page.getViewport({ scale: 1.5 });
                    const canvas = document.createElement("canvas");
                    pdfCanvasContainer.appendChild(canvas);

                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    const ctx = canvas.getContext('2d');

                    const renderContext = {
                        canvasContext: ctx,
                        viewport: viewport,
                    };

                    page.render(renderContext);
                });
            }
        }).catch((error) => {
            console.error("Error al cargar el PDF:", error);
            alert("No se pudo cargar el archivo PDF.");
        });
    }

    generateBtn.addEventListener("click", () => {
        if (!uploadedPdfPath) {
            alert("Primero sube un archivo.");
            return;
        }

        generateBtn.style.display = "none";
        outputContainer.style.display = "block";
        document.getElementById('loading-indicator').style.display = "block";

        fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileName: uploadedPdfPath })
        })
        .catch(error => {
            console.error("Error al generar:", error);
            alert("Error al iniciar el proceso.");
        });
    });
    
    
    async function startSequentialChecks(uniqueName, outputFilePath) {
        try {
            // 1. Comprobar existencia del archivo periódicamente
            await waitForFileExistence(uniqueName);

            document.getElementById('loading-indicator').style.display = "none"; // Ocultar rueda de carga
            document.getElementById('loading-message').style.display = "none"; // Ocultar rueda de carga

            // 2. Obtener contenido periódicamente
            await fetchFileContent(outputFilePath);
        } catch (error) {
            console.error("Error en el proceso de chequeo secuencial:", error);
        }
    }
    
    async function waitForFileExistence(uniqueName) {
        while (true) {
            try {
                const response = await fetch('/checkFile/' + encodeURIComponent(uniqueName));
                if (response.ok) {
                    console.log("Archivo encontrado:", uniqueName);
                    return; // Salir del bucle cuando el archivo exista
                }
                if (response.status !== 404) {
                    throw new Error("Error al comprobar la existencia del archivo.");
                }
            } catch (error) {
                console.error("Error durante la comprobación de existencia:", error);
            }
    
            // Esperar 1 segundo antes de la siguiente comprobación
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    
    
    async function fetchFileContent(outputFilePath) {
        const timeLimit = Date.now() + 1200000; // Limitar el tiempo total a 5 minutos
    
        while (Date.now() < timeLimit) {
            try {
                const response = await fetch(outputFilePath);
                if (response.ok) {
                    const text = await response.text();
                    if (text) {
                        outputContent.innerHTML = markdown.toHTML(text);
                        
                        // Seleccionamos los elementos de texto dentro del contenido
                        const markdownElements = outputContent.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li');
                        
                        // Aplicamos la clase de transición gradual a los elementos
                        markdownElements.forEach((element) => {
                            element.classList.add('markdown-text');
                        });
    
                        // Esperamos un pequeño tiempo para que el navegador haga el redibujado
                        setTimeout(() => {
                            // Cambiamos el color a uno más oscuro, lo que activará la transición
                            markdownElements.forEach((element) => {
                                element.style.color = '#333'; // Color más oscuro
                            });
                        }, 50); // Pequeño retraso para asegurar el redibujado
                    }
                } else {
                    console.warn("Archivo aún no disponible, reintentando...");
                }
            } catch (error) {
                console.error("Error durante la obtención del contenido:", error);
            }
    
            // Esperar 100 ms antes de la siguiente solicitud
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    
        console.warn("Tiempo límite alcanzado. Deteniendo actualizaciones.");
    }
    
    
    
});
