const express = require('express');
const path = require('path');
const cors = require('cors'); // 1. IMPORTANTE: Importamos CORS
const app = express();
const PORT = 3000;

app.use(cors()); // 2. IMPORTANTE: Habilitamos CORS para aceptar peticiones de Live Server (puerto 5500)
app.use(express.json());

// Servir el archivo index.html directamente (Corregido 'Brune' por 'res')
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'checklistTurbina.html'));
});

// Base de datos temporal en memoria
let usuariosRegistrados = new Set();
let checklistActual = null;
let necesitaActualizacion = false;
let temporizadorReinicio = null;

// TIEMPO DE REINICIO: Cambia a (60 * 1000) si quieres probarlo en 1 minuto en vez de 1 hora.
const TIEMPO_REINICIO = 60 * 60 * 1000; 

// Endpoint 1: Login y almacenamiento de correo
app.post('/api/login', (req, res) => {
    const { email } = req.body;
    if (email) {
        usuariosRegistrados.add(email);
        console.log(`[LOGIN] Correo almacenado para notificaciones: ${email}`);
    }
    res.json({ status: "success", message: "Usuario registrado" });
});

// Endpoint 2: Guardar el checklist y activar la cuenta regresiva de 1 hora
app.post('/api/checklist', (req, res) => {
    checklistActual = req.body;
    necesitaActualizacion = false;
    console.log('[DATOS] Nuevo checklist recibido:', checklistActual);

    // Si ya había un temporizador corriendo, lo cancelamos para iniciar uno nuevo
    if (temporizadorReinicio) clearTimeout(temporizadorReinicio);

    // Iniciar temporizador de 1 hora
        temporizadorReinicio = setTimeout(() => {
        checklistActual = null; // Reiniciar valores (Vaciar checklist)
        necesitaActualizacion = true;
        console.log('\n--- ⏰ HORA CUMPLIDA: EL CHECKLIST SE HA REINICIADO ---');
        
        // Simulación de envío de correos de notificación a todos los usuarios
        usuariosRegistrados.forEach(email => {
            console.log(`[NOTIFICACIÓN ENVIADA] 📧 Para: ${email}`);
            console.log(`Mensaje: "Hola, los valores de la turbina se han reiniciado. Por favor ingresa al sistema para actualizar el checklist diario."`);
        });
        
    }, TIEMPO_REINICIO);

    res.json({ status: "success", message: "Checklist guardado. Temporizador de 1 hora iniciado." });
});

// Endpoint 3: El cliente pregunta constantemente si los datos ya caducaron
app.get('/api/status', (req, res) => {
    res.json({ reinstalado: necesitaActualizacion });
});

app.listen(PORT, () => {
    console.log(`Servidor ejecutándose en http://localhost:${PORT}`);
    console.log(`Prueba cambiando TIEMPO_REINICIO a 60000 (1 minuto) en el código para testear rápido.`);
});

