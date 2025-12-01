let ritmoChart;
let historialData = [];
let tiempoData = [];

// Inicializar gráfico
function inicializarGrafico() {
    const ctx = document.getElementById('ritmoChart').getContext('2d');
    
    // Destruir gráfico existente si hay uno
    if (ritmoChart) {
        ritmoChart.destroy();
    }
    
    ritmoChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: tiempoData,
            datasets: [{
                label: 'Ritmo Cardíaco (lpm)',
                data: historialData,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#dc3545',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Latidos por Minuto (lpm)'
                    },
                    min: 40,
                    max: 120
                },
                x: {
                    title: {
                        display: true,
                        text: 'Tiempo'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            }
        }
    });
}

// Cargar datos iniciales
async function cargarDatosIniciales() {
    try {
        console.log('Cargando datos para paciente:', pacienteId);
        const response = await fetch(`/api/ritmo/${pacienteId}`);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const datos = await response.json();
        console.log('Datos recibidos:', datos);
        
        if (datos.error) {
            throw new Error(datos.error);
        }
        
        // Procesar datos para el gráfico (últimos 20 registros)
        const datosRecientes = datos.slice(0, 20).reverse();
        
        historialData = datosRecientes.map(item => item.ritmo);
        tiempoData = datosRecientes.map(item => {
            if (item.fecha_registro) {
                const date = new Date(item.fecha_registro);
                return date.toLocaleTimeString();
            }
            return '--:--:--';
        });
        
        // Actualizar tabla de historial
        actualizarTablaHistorial(datos.slice(0, 10));
        
        // Cargar estadísticas
        await cargarEstadisticas();
        
        // Inicializar gráfico
        inicializarGrafico();
        
    } catch (error) {
        console.error('Error cargando datos:', error);
        document.getElementById('historial-table').innerHTML = 
            '<tr><td colspan="3" class="text-center text-danger">Error cargando datos: ' + error.message + '</td></tr>';
    }
}

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        const response = await fetch(`/api/estadisticas/${pacienteId}`);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const stats = await response.json();
        console.log('Estadísticas recibidas:', stats);
        
        if (stats.error) {
            throw new Error(stats.error);
        }
        
        document.getElementById('ritmo-promedio').textContent = 
            stats.promedio ? Math.round(stats.promedio) : '--';
        document.getElementById('ritmo-maximo').textContent = 
            stats.maximo || '--';
        document.getElementById('ritmo-minimo').textContent = 
            stats.minimo || '--';
            
        // Actualizar ritmo actual (último registro)
        if (historialData.length > 0) {
            document.getElementById('ritmo-actual').textContent = 
                historialData[historialData.length - 1];
        } else {
            document.getElementById('ritmo-actual').textContent = '--';
        }
        
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        document.getElementById('ritmo-promedio').textContent = 'Error';
        document.getElementById('ritmo-maximo').textContent = 'Error';
        document.getElementById('ritmo-minimo').textContent = 'Error';
        document.getElementById('ritmo-actual').textContent = 'Error';
    }
}

// Actualizar tabla de historial
function actualizarTablaHistorial(datos) {
    const tbody = document.getElementById('historial-table');
    
    if (!datos || datos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center">No hay datos registrados</td></tr>';
        return;
    }
    
    let html = '';
    
    datos.forEach(item => {
        // Determinar clase según el ritmo
        let estadoClass = '';
        let estadoText = '';
        const ritmo = item.ritmo;
        
        if (ritmo > 100) {
            estadoClass = 'ritmo-alto';
            estadoText = 'Alto';
        } else if (ritmo < 60) {
            estadoClass = 'ritmo-bajo';
            estadoText = 'Bajo';
        } else {
            estadoClass = 'ritmo-normal';
            estadoText = 'Normal';
        }
        
        html += `
            <tr>
                <td>${item.fecha_registro || '--'}</td>
                <td>${ritmo} lpm</td>
                <td><span class="${estadoClass} fw-bold">${estadoText}</span></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Simular datos en tiempo real (para pruebas/demo)
function simularDatosTiempoReal() {
    // Solo simular si hay datos existentes
    if (historialData.length === 0) {
        console.log('No hay datos existentes para simular');
        return;
    }
    
    setInterval(() => {
        // En una aplicación real, esto vendría del dispositivo
        const nuevoRitmo = Math.floor(Math.random() * 40) + 60; // 60-100 lpm
        
        // Actualizar gráfico
        const ahora = new Date().toLocaleTimeString();
        
        if (historialData.length >= 20) {
            historialData.shift();
            tiempoData.shift();
        }
        
        historialData.push(nuevoRitmo);
        tiempoData.push(ahora);
        
        // Actualizar gráfico si existe
        if (ritmoChart) {
            ritmoChart.data.labels = tiempoData;
            ritmoChart.data.datasets[0].data = historialData;
            ritmoChart.update('none');
        }
        
        // Actualizar display
        document.getElementById('ritmo-actual').textContent = nuevoRitmo;
        
        // Agregar a la tabla (solo para demo)
        agregarNuevoRegistroTabla(nuevoRitmo, ahora);
        
    }, 5000); // Actualizar cada 5 segundos
}

// Función auxiliar para agregar nuevo registro a la tabla (solo para demo)
function agregarNuevoRegistroTabla(ritmo, tiempo) {
    const tbody = document.getElementById('historial-table');
    const filas = tbody.getElementsByTagName('tr');
    
    // Determinar estado
    let estadoClass = '';
    let estadoText = '';
    
    if (ritmo > 100) {
        estadoClass = 'ritmo-alto';
        estadoText = 'Alto';
    } else if (ritmo < 60) {
        estadoClass = 'ritmo-bajo';
        estadoText = 'Bajo';
    } else {
        estadoClass = 'ritmo-normal';
        estadoText = 'Normal';
    }
    
    const nuevaFila = `
        <tr>
            <td>${tiempo}</td>
            <td>${ritmo} lpm</td>
            <td><span class="${estadoClass} fw-bold">${estadoText}</span></td>
        </tr>
    `;
    
    // Insertar al principio de la tabla
    if (filas.length > 0 && !filas[0].querySelector('td[colspan]')) {
        tbody.insertAdjacentHTML('afterbegin', nuevaFila);
        
        // Mantener máximo 10 filas en la tabla
        if (filas.length >= 10) {
            tbody.removeChild(filas[filas.length - 1]);
        }
    }
}

// Inicializar cuando se cargue la página
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard inicializado para paciente:', pacienteId);
    
    // Cargar datos iniciales
    cargarDatosIniciales().then(() => {
        console.log('Datos iniciales cargados correctamente');
        
        // Solo para demostración - en producción esto vendría del dispositivo real
        setTimeout(() => {
            console.log('Iniciando simulación de datos en tiempo real');
            simularDatosTiempoReal();
        }, 3000);
    }).catch(error => {
        console.error('Error en la inicialización:', error);
    });
});