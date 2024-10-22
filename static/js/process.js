// static/js/process.js

document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const videoForm = document.getElementById('video-form');
    const progressSection = document.getElementById('progress-section');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const resultSection = document.getElementById('result-section');
    const sugerenciasPre = document.getElementById('sugerencias');

    videoForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const urlVideo = document.getElementById('url_video').value;

        // Mostrar la sección de progreso
        progressSection.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = 'Iniciando el procesamiento...';

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
                // Escuchar eventos relacionados con la sesión
                socket.emit('join', data.session_id);
            } else if (data.error) {
                alert(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al iniciar el procesamiento.');
        });
    });

    // Escuchar eventos de progreso
    socket.on('progreso', (data) => {
        const { step, total_steps, data: mensaje } = data;
        const porcentaje = (step / total_steps) * 100;
        progressBar.style.width = `${porcentaje}%`;
        progressBar.setAttribute('aria-valuenow', porcentaje);
        progressText.textContent = mensaje;
    });

    // Escuchar evento de resultado
    socket.on('resultado', (data) => {
        const { sugerencias } = data;
        sugerenciasPre.textContent = sugerencias;
        resultSection.style.display = 'block';
        progressSection.style.display = 'none';
    });

    // Escuchar evento de error
    socket.on('error', (data) => {
        const { data: mensaje } = data;
        alert(`Error: ${mensaje}`);
        progressSection.style.display = 'none';
    });
});
