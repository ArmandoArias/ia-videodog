// static/js/process.js

document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const videoForm = document.getElementById('video-form');
    const progressSection = document.getElementById('progress-section');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const spinner = document.getElementById('spinner'); // Spinner de carga
    const resultSection = document.getElementById('result-section');
    const sugerenciasContainer = document.getElementById('sugerencias');
    const processButton = document.getElementById('process-button'); // Botón "Procesar"

    // Configuración de Toastr (opcional, para personalizar notificaciones)
    toastr.options = {
        "closeButton": true,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "timeOut": "3000"
    };

    socket.on('connect', () => {
        console.log('Conectado a Socket.IO');
    });

    videoForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const urlVideo = document.getElementById('url_video').value.trim();

        // Validar la URL en el frontend
        if (!isValidYouTubeUrl(urlVideo)) {
            toastr.error('Por favor, ingresa una URL válida de YouTube.');
            return;
        }

        // Desactivar el botón "Procesar" y cambiar su texto
        processButton.disabled = true;
        processButton.textContent = 'Procesando...';

        // Mostrar la sección de progreso y spinner
        progressSection.style.display = 'block';
        spinner.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressText.textContent = 'Iniciando el procesamiento...';

        // Ocultar la sección de resultados si estaba visible
        resultSection.style.display = 'none';
        sugerenciasContainer.innerHTML = '';

        // Enviar la solicitud al servidor
        fetch('/procesar_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 'url_video': urlVideo })
        })
        .then(response => response.json())
        .then(data => {
            if (data.session_id) {
                console.log('Unido a la sala:', data.session_id);
                // Unirse a la sala correspondiente
                socket.emit('join', { 'session_id': data.session_id });
            } else if (data.error) {
                toastr.error(data.error);
                // Reactivar el botón "Procesar" y restablecer su texto
                processButton.disabled = false;
                processButton.textContent = 'Procesar';
                progressSection.style.display = 'none';
                spinner.style.display = 'none';
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            toastr.error('Ocurrió un error al iniciar el procesamiento.');
            // Reactivar el botón "Procesar" y restablecer su texto
            processButton.disabled = false;
            processButton.textContent = 'Procesar';
            progressSection.style.display = 'none';
            spinner.style.display = 'none';
        });
    });

    // Escuchar eventos de progreso
    socket.on('progreso', (data) => {
        console.log('Evento progreso recibido:', data);
        const { step, total_steps, data: mensaje } = data;
        const porcentaje = Math.round((step / total_steps) * 100);
        progressBar.style.width = `${porcentaje}%`;
        progressBar.setAttribute('aria-valuenow', porcentaje);
        progressText.textContent = mensaje;
    });

    // Escuchar evento de resultado
    socket.on('resultado', (data) => {
        console.log('Evento resultado recibido:', data);
        const { sugerencias } = data;

        // Limpiar cualquier sugerencia previa
        sugerenciasContainer.innerHTML = '';

        // Iterar sobre las sugerencias y mostrarlas
        for (const [key, value] of Object.entries(sugerencias)) {
            // Normalizar la clave para eliminar acentos
            const normalizedKey = key.normalize('NFD').replace(/[\u0300-\u036f]/g, "").toLowerCase();

            if (normalizedKey.includes('titulo')) {
                // Crear tarjeta para el título
                const card = document.createElement('div');
                card.className = 'card mb-3';
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body d-flex justify-content-between align-items-center';
                
                const title = document.createElement('h5');
                title.className = 'card-title mb-0';
                title.textContent = `${key}: ${value}`;
                
                const copyButton = document.createElement('button');
                copyButton.className = 'btn btn-outline-primary btn-sm';
                copyButton.textContent = 'Copiar';
                copyButton.addEventListener('click', () => {
                    navigator.clipboard.writeText(value)
                        .then(() => {
                            toastr.success(`Título copiado: ${value}`);
                        })
                        .catch(err => {
                            toastr.error('Error al copiar el título.');
                            console.error('Error al copiar:', err);
                        });
                });

                cardBody.appendChild(title);
                cardBody.appendChild(copyButton);
                card.appendChild(cardBody);
                sugerenciasContainer.appendChild(card);
            } else if (normalizedKey.includes('resumen')) {
                // Crear tarjeta para el resumen
                const card = document.createElement('div');
                card.className = 'card mb-3';
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                
                const summaryTitle = document.createElement('h5');
                summaryTitle.className = 'card-title';
                summaryTitle.textContent = 'Resumen:';
                
                const summaryText = document.createElement('p');
                summaryText.className = 'card-text';
                summaryText.textContent = value;

                // Botón para copiar el resumen
                const copyButton = document.createElement('button');
                copyButton.className = 'btn btn-outline-primary btn-sm mt-2';
                copyButton.textContent = 'Copiar Resumen';
                copyButton.addEventListener('click', () => {
                    navigator.clipboard.writeText(value)
                        .then(() => {
                            toastr.success('Resumen copiado al portapapeles.');
                        })
                        .catch(err => {
                            toastr.error('Error al copiar el resumen.');
                            console.error('Error al copiar:', err);
                        });
                });

                cardBody.appendChild(summaryTitle);
                cardBody.appendChild(summaryText);
                cardBody.appendChild(copyButton);
                card.appendChild(cardBody);
                sugerenciasContainer.appendChild(card);
            }
        }

        // Mostrar la sección de resultados y ocultar el progreso y spinner
        resultSection.style.display = 'block';
        progressSection.style.display = 'none';
        spinner.style.display = 'none';

        // Reactivar el botón "Procesar" y restablecer su texto
        processButton.disabled = false;
        processButton.textContent = 'Procesar';
    });

    // Escuchar evento de error
    socket.on('error', (data) => {
        console.log('Evento error recibido:', data);
        const { data: mensaje } = data;
        toastr.error(`Error: ${mensaje}`);
        progressSection.style.display = 'none';
        spinner.style.display = 'none';

        // Reactivar el botón "Procesar" y restablecer su texto
        processButton.disabled = false;
        processButton.textContent = 'Procesar';
    });

    // Función para validar URLs de YouTube
    function isValidYouTubeUrl(url) {
        const pattern = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;
        return pattern.test(url);
    }
});
