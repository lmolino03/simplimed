const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');
const { v4: uuidv4 } = require('uuid');


const { spawn } = require('child_process');
let scriptProcess = null;


const app = express();
const port = 3000;

app.use(express.json());

const localProductionFolder = path.join(__dirname, '../data/ProductionData');
const localOutputFolder = path.join(__dirname, '../data/OutputData');
const localRunScript = path.join(__dirname, './run_backend.sh'); // Asumiendo que ahora el script es local

const H_localProductionFolder = path.join(__dirname, '../data/H_ProductionData');
const H_localOutputFolder = path.join(__dirname, '../data/H_OutputData');

// Archivos estáticos y vistas
app.use('/public', express.static(path.join(__dirname, 'public')));
app.use('/ProductionData', express.static(path.join(__dirname, '../data/ProductionData')));
app.use('/tempUploads', express.static(path.join(__dirname, './tempUploads')));


app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'public/views', 'index.html')));
app.get('/performance', (req, res) => res.sendFile(path.join(__dirname, 'public/views', 'performance.html')));
app.get('/preview', (req, res) => res.sendFile(path.join(__dirname, 'public/views', 'preview.html')));



// Asegurar existencia de carpetas necesarias
[localProductionFolder, localOutputFolder, './tempUploads'].forEach(folder => {
    if (!fs.existsSync(folder)) {
        fs.mkdirSync(folder, { recursive: true });
    }
});

const clients = []; // Esto debe estar fuera de cualquier handler, en el ámbito global del servidor




function sendChunkToClient(clientId, chunk, fileName) {
    const client = clients.find(c => c.id === clientId);
    if (client) {
        client.res.write(`data: ${JSON.stringify({
            type: 'fileChunk',
            chunk: chunk,
            fileName: fileName
        })}\n\n`);
    }
}




// Configurar multer
const storage = multer.diskStorage({
    destination: (req, file, cb) => cb(null, './tempUploads'),
    filename: (req, file, cb) => cb(null, uuidv4() + '.pdf')
});
const upload = multer({ storage: storage });



app.post('/upload', upload.single('file'), (req, res) => {
    if (!req.file) return res.status(400).send({ message: 'No file uploaded' });

    // Ruta completa del archivo subido
    const localTempPath = path.join(__dirname, 'tempUploads', req.file.filename);

    console.log(`[SERVER] [UPLOAD] Archivo recibido en temporal: ${localTempPath}`);

    // Enviar el nombre del archivo a la respuesta
    res.status(200).send({ message: 'Archivo subido correctamente', fileName: req.file.filename });
});





// Endpoint para manejar la conexión SSE
app.get('/events', (req, res) => {
    const clientId = req.query.clientId;
    if (!clientId) return res.status(400).send('Falta clientId (usa el nombre del archivo)');

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();

    clients.push({ id: clientId, res });

    req.on('close', () => {
        const index = clients.findIndex(c => c.id === clientId);
        if (index !== -1) clients.splice(index, 1);
    });
});


// Función para enviar un evento a todos los clientes conectados
function sendSSEMessage(message) {
    clients.forEach(client => {
        client.write(`data: ${JSON.stringify(message)}\n\n`);
    });
}





// Lanzar procesamiento con script local
const chokidar = require('chokidar'); // npm install chokidar si no lo tienes

app.post('/generate', (req, res) => {
    const { fileName } = req.body;
    if (!fileName) return res.status(400).send({ message: 'Falta el nombre del archivo.' });

    const clientId = fileName;

    const localTempPath = path.join(__dirname, 'tempUploads', fileName);
    const prodPath = path.join(localProductionFolder, fileName);
    const outputFileName = fileName.replace('.pdf', '.md');
    const outputFilePath = path.join(localOutputFolder, outputFileName);

    fs.copyFile(localTempPath, prodPath, (err) => {
        if (err) return res.status(500).json({ message: 'Error al copiar el archivo.' });

        console.log(`Archivo ${fileName} copiado correctamente`);

        let lastSize = 0;

        const watcher = chokidar.watch(outputFilePath, { usePolling: true, interval: 50 });

        watcher.on('change', () => {
            fs.stat(outputFilePath, (err, stats) => {
                if (err) return;

                const newSize = stats.size;

                if (newSize > lastSize) {
                    const stream = fs.createReadStream(outputFilePath, {
                        start: lastSize,
                        end: newSize
                    });

                    stream.on('data', chunk => {
                        sendChunkToClient(clientId, chunk.toString(), outputFileName);
                    });

                    lastSize = newSize;
                }
            });
        });

        res.status(200).json({ message: 'Generación iniciada', fileName });
    });
});



app.post('/notifyPreviewExit', upload.single('file'), async (req, res) => {
    const { fileName } = req.body;

    if (!fileName) {
        return res.status(400).json({ message: 'No se ha proporcionado el nombre del archivo.' });
    }
    console.log('El cliente ha salido');

    const localTempPath = path.join(__dirname, 'tempUploads', fileName);
    const filename_md = path.basename(fileName, '.pdf') + '.md';

    const prodPath = path.join(H_localProductionFolder, fileName);
    const outPath = path.join(H_localOutputFolder, filename_md);

    const localProdFolderPath = path.join(localProductionFolder, fileName);
    const localOutFolderPath = path.join(localOutputFolder, filename_md);

    try {
        console.log(`Intentando eliminar el archivo: ${localProdFolderPath}`);
        if (fs.existsSync(localProdFolderPath)) {
            fs.unlinkSync(localProdFolderPath);
            console.log(`[SERVER] Archivo existente borrado en localProductionFolder: ${localProdFolderPath}`);
        }

        await fs.promises.copyFile(localTempPath, prodPath);
        fs.unlinkSync(localTempPath);

        console.log(`Intentando eliminar el archivo: ${localOutFolderPath}`);
        if (fs.existsSync(localOutFolderPath)) {
            await fs.promises.copyFile(localOutFolderPath, outPath);
            fs.unlinkSync(localOutFolderPath);
        }

        return res.status(200).send({ message: 'Archivos copiados correctamente', fileName });
    } catch (err) {
        console.error('Error en el proceso de copia/eliminación:', err);
        return res.status(500).json({ message: 'Error al procesar archivos.' });
    }
});


app.get('/stream', (req, res) => {
    res.set({
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    res.flushHeaders();

    const interval = setInterval(() => {
        const filePath = 'output.txt';
        if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf-8');
            res.write(`data: ${content.replace(/\n/g, '\\n')}\n\n`);
        }
    }, 1000); // o sólo una vez si sabes cuándo enviar

    req.on('close', () => {
        clearInterval(interval);
        res.end();
    });
});



















// Comprobar si el archivo de salida existe
app.get('/checkFile/:uniqueName', (req, res) => {
    const localPath = path.join(localOutputFolder, req.params.uniqueName);

    if (fs.existsSync(localPath)) {
        res.status(200).send("El archivo está disponible.");
    } else {
        res.status(404).send("El archivo no está disponible.");
    }
});

// Obtener contenido de archivo de salida
app.get('/OutputData/:uniqueName', (req, res) => {
    const localPath = path.join(localOutputFolder, req.params.uniqueName);

    if (fs.existsSync(localPath)) {
        const content = fs.readFileSync(localPath, 'utf8');
        res.status(200).send(content);
    } else {
        res.status(404).send("El archivo no está disponible.");
    }
});



// Iniciar servidor
app.listen(port, () => {
    console.log(`[SERVER] Servidor ejecutándose en http://localhost:${port}`);

    console.log("[SERVER] Lanzando script persistente de backend...");
    scriptProcess = spawn('bash', [localRunScript]);

    scriptProcess.stdout.on('data', data => {
        console.log(`[SERVER][SCRIPT] ${data.toString()}`);
    });

    scriptProcess.stderr.on('data', data => {
        console.error(`[SERVER][SCRIPT ERROR] ${data.toString()}`);
    });

    scriptProcess.on('close', code => {
        console.log(`[SERVER] Script finalizado con código ${code}`);
    });
});


// Detener el script al cerrar el servidor
process.on('SIGINT', () => {
    console.log('\nDeteniendo servidor y script...');
    if (scriptProcess) scriptProcess.kill('SIGTERM');
    process.exit();
});

process.on('exit', () => {
    if (scriptProcess) scriptProcess.kill('SIGTERM');
});
