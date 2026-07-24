// Configuración de la API
const API_BASE = '/api/v1';

// Estado global
let mascotas = [];
let emociones = [];
let intensidadSeleccionada = 2;
let chartGlobal = null;
let chartMascota = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    inicializarPagina();
    setupIntensidadSelector();
});

async function inicializarPagina() {
    await Promise.all([
        cargarMascotas(),
        cargarEmociones(),
        cargarEstadisticas()
    ]);
    actualizarSelectores();
}

// Navegación entre secciones
function showSection(seccion) {
    document.querySelectorAll('[id^="section-"]').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
    document.getElementById(`section-${seccion}`).style.display = 'block';
    event.target.classList.add('active');
    
    if (seccion === 'estadisticas') {
        cargarEstadisticas();
    }
}

// ==================== MASCOTAS ====================

async function cargarMascotas() {
    try {
        const response = await fetch(`${API_BASE}/mascotas`);
        mascotas = await response.json();
        renderMascotas();
        document.getElementById('total-mascotas').textContent = mascotas.length;
    } catch (error) {
        showToast('Error al cargar mascotas', 'error');
    }
}

function renderMascotas() {
    const tbody = document.getElementById('mascotas-tbody');
    const emptyState = document.getElementById('mascotas-empty');
    
    if (mascotas.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    tbody.innerHTML = mascotas.map(m => `
        <tr data-id="${m.id}">
            <td>
                <div class="flex items-center gap-1">
                    <div class="pet-avatar">${getEmojiEspecie(m.especie)}</div>
                    <strong>${m.nombre}</strong>
                </div>
            </td>
            <td>${capitalize(m.especie)}</td>
            <td>${m.raza || '-'}</td>
            <td><span class="emocion-badge emocion-tranquilo">${m.total_emociones} emociones</span></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editarMascota(${m.id})">✏️</button>
                <button class="btn btn-sm btn-success" onclick="irARegistrarEmocion(${m.id})">💭</button>
            </td>
        </tr>
    `).join('');
}

function filtrarMascotas() {
    const searchTerm = document.getElementById('search-mascotas').value.toLowerCase();
    const filas = document.querySelectorAll('#mascotas-tbody tr');
    
    filas.forEach(fila => {
        const texto = fila.textContent.toLowerCase();
        fila.style.display = texto.includes(searchTerm) ? '' : 'none';
    });
}

function openMascotaModal(id = null) {
    const modal = document.getElementById('mascota-modal');
    const form = document.getElementById('mascota-form');
    const title = document.getElementById('mascota-modal-title');
    
    form.reset();
    document.getElementById('mascota-id').value = '';
    
    if (id) {
        title.textContent = '✏️ Editar Mascota';
        const mascota = mascotas.find(m => m.id === id);
        if (mascota) {
            document.getElementById('mascota-id').value = mascota.id;
            document.getElementById('mascota-nombre').value = mascota.nombre;
            document.getElementById('mascota-especie').value = mascota.especie;
            document.getElementById('mascota-raza').value = mascota.raza || '';
            document.getElementById('mascota-notas').value = '';
        }
    } else {
        title.textContent = '🐾 Nueva Mascota';
    }
    
    modal.classList.add('active');
}

function closeMascotaModal() {
    document.getElementById('mascota-modal').classList.remove('active');
}

async function guardarMascota(event) {
    event.preventDefault();
    
    const id = document.getElementById('mascota-id').value;
    const data = {
        nombre: document.getElementById('mascota-nombre').value,
        especie: document.getElementById('mascota-especie').value,
        raza: document.getElementById('mascota-raza').value || null,
        fecha_nacimiento: document.getElementById('mascota-fecha').value || null,
        notas: document.getElementById('mascota-notas').value || null
    };
    
    try {
        const url = id ? `${API_BASE}/mascotas/${id}` : `${API_BASE}/mascotas`;
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast(id ? 'Mascota actualizada' : 'Mascota creada', 'success');
            closeMascotaModal();
            await cargarMascotas();
            actualizarSelectores();
        } else {
            showToast('Error al guardar', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    }
}

function editarMascota(id) {
    openMascotaModal(id);
}

async function confirmDeleteMascota() {
    const id = document.getElementById('mascota-id').value;
    if (!id) return;
    
    if (confirm('¿Estás seguro de eliminar esta mascota? Se eliminarán todas sus emociones.')) {
        try {
            const response = await fetch(`${API_BASE}/mascotas/${id}`, { method: 'DELETE' });
            if (response.ok) {
                showToast('Mascota eliminada', 'success');
                closeMascotaModal();
                await Promise.all([cargarMascotas(), cargarEmociones()]);
                actualizarSelectores();
            }
        } catch (error) {
            showToast('Error al eliminar', 'error');
        }
    }
}

function irARegistrarEmocion(mascotaId) {
    showSection('emociones');
    document.getElementById('emocion-mascota').value = mascotaId;
}

// ==================== EMOCIONES ====================

async function cargarEmociones() {
    try {
        const response = await fetch(`${API_BASE}/emociones`);
        emociones = await response.json();
        renderEmociones();
        document.getElementById('total-emociones').textContent = emociones.length;
    } catch (error) {
        showToast('Error al cargar emociones', 'error');
    }
}

function renderEmociones() {
    const tbody = document.getElementById('emociones-tbody');
    const emptyState = document.getElementById('emociones-empty');
    const filtroMascota = document.getElementById('filtro-mascota').value;
    
    let emocionesFiltradas = emociones;
    if (filtroMascota) {
        emocionesFiltradas = emociones.filter(e => e.mascota_id === parseInt(filtroMascota));
    }
    
    if (emocionesFiltradas.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    tbody.innerHTML = emocionesFiltradas.map(e => `
        <tr data-id="${e.id}">
            <td>${formatDate(e.fecha_hora)}</td>
            <td>${getNombreMascota(e.mascota_id)}</td>
            <td><span class="emocion-badge emocion-${e.tipo}">${getEmojiEmocion(e.tipo)} ${capitalize(e.tipo)}</span></td>
            <td>
                <div class="intensidad-indicator">
                    ${[1,2,3,4,5].map(i => `<div class="intensidad-dot ${i <= e.intensidad ? 'active' : ''}"></div>`).join('')}
                </div>
            </td>
            <td>${e.contexto ? getEmojiContexto(e.contexto) + ' ' + capitalize(e.contexto.replace('_', ' ')) : '-'}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="eliminarEmocion(${e.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function filtrarEmociones() {
    const searchTerm = document.getElementById('search-emociones').value.toLowerCase();
    const filas = document.querySelectorAll('#emociones-tbody tr');
    
    filas.forEach(fila => {
        const texto = fila.textContent.toLowerCase();
        fila.style.display = texto.includes(searchTerm) ? '' : 'none';
    });
}

function setupIntensidadSelector() {
    const selector = document.getElementById('intensidad-selector');
    selector.querySelectorAll('.intensidad-dot').forEach(dot => {
        dot.addEventListener('click', () => {
            const value = parseInt(dot.dataset.value);
            intensidadSeleccionada = value;
            document.getElementById('emocion-intensidad').value = value;
            selector.querySelectorAll('.intensidad-dot').forEach((d, i) => {
                d.classList.toggle('active', i < value);
            });
        });
    });
}

async function registrarEmocion(event) {
    event.preventDefault();
    
    const data = {
        mascota_id: parseInt(document.getElementById('emocion-mascota').value),
        tipo: document.getElementById('emocion-tipo').value,
        intensidad: intensidadSeleccionada,
        contexto: document.getElementById('emocion-contexto').value || null,
        descripcion: document.getElementById('emocion-descripcion').value || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/emociones`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Emoción registrada', 'success');
            event.target.reset();
            intensidadSeleccionada = 2;
            document.getElementById('emocion-intensidad').value = 2;
            setupIntensidadSelector();
            await Promise.all([cargarEmociones(), cargarMascotas(), cargarEstadisticas()]);
        } else {
            showToast('Error al registrar', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    }
}

async function eliminarEmocion(id) {
    if (confirm('¿Eliminar esta emoción?')) {
        try {
            const response = await fetch(`${API_BASE}/emociones/${id}`, { method: 'DELETE' });
            if (response.ok) {
                showToast('Emoción eliminada', 'success');
                await Promise.all([cargarEmociones(), cargarMascotas(), cargarEstadisticas()]);
            }
        } catch (error) {
            showToast('Error al eliminar', 'error');
        }
    }
}

// ==================== ESTADÍSTICAS ====================

async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_BASE}/emociones/stats`);
        const data = await response.json();
        
        document.getElementById('stat-total-emociones').textContent = data.total || 0;
        
        if (data.stats && data.stats.length > 0) {
            const masFrecuente = data.stats.reduce((a, b) => a.count > b.count ? a : b);
            document.getElementById('stat-emocion-frecuente').textContent = capitalize(masFrecuente.tipo);
        }
        
        renderStatsChart(data.stats || []);
        renderStatsList(data.stats || []);
        
        // Cargar selector de mascotas para stats
        const select = document.getElementById('stats-mascota-select');
        select.innerHTML = '<option value="">Selecciona una mascota</option>' +
            mascotas.map(m => `<option value="${m.id}">${m.nombre}</option>`).join('');
        
    } catch (error) {
        showToast('Error al cargar estadísticas', 'error');
    }
}

function renderStatsChart(stats) {
    const ctx = document.getElementById('chart-emociones').getContext('2d');
    
    if (chartGlobal) {
        chartGlobal.destroy();
    }
    
    const colores = {
        feliz: '#00b894',
        triste: '#0984e3',
        ansioso: '#fdcb6e',
        tranquilo: '#636e72',
        jugueton: '#e17055',
        asustado: '#2d3436',
        enfermizo: '#55efc4',
        cansado: '#74b9ff',
        excitado: '#f39c12',
        confundido: '#9b59b6'
    };
    
    chartGlobal = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: stats.map(s => capitalize(s.tipo)),
            datasets: [{
                data: stats.map(s => s.count),
                backgroundColor: stats.map(s => colores[s.tipo] || '#6c5ce7'),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function renderStatsList(stats) {
    const container = document.getElementById('stats-list');
    
    if (stats.length === 0) {
        container.innerHTML = '<p class="text-center text-gray">No hay datos</p>';
        return;
    }
    
    container.innerHTML = stats.map(s => `
        <div class="flex items-center justify-between mb-1" style="padding: 10px; background: var(--light); border-radius: 8px;">
            <span class="emocion-badge emocion-${s.tipo}">${getEmojiEmocion(s.tipo)} ${capitalize(s.tipo)}</span>
            <div>
                <strong>${s.count}</strong> (${s.percentage}%)
                <span style="color: var(--gray); font-size: 0.85rem;">avg: ${s.avg_intensidad.toFixed(1)}</span>
            </div>
        </div>
    `).join('');
}

async function cargarStatsMascota() {
    const mascotaId = document.getElementById('stats-mascota-select').value;
    
    if (!mascotaId) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/emociones/stats?mascota_id=${mascotaId}`);
        const data = await response.json();
        
        const ctx = document.getElementById('chart-mascota').getContext('2d');
        
        if (chartMascota) {
            chartMascota.destroy();
        }
        
        const colores = {
            feliz: '#00b894',
            triste: '#0984e3',
            ansioso: '#fdcb6e',
            tranquilo: '#636e72',
            jugueton: '#e17055',
            asustado: '#2d3436',
            enfermizo: '#55efc4',
            cansado: '#74b9ff',
            excitado: '#f39c12',
            confundido: '#9b59b6'
        };
        
        chartMascota = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.stats.map(s => capitalize(s.tipo)),
                datasets: [{
                    label: 'Cantidad',
                    data: data.stats.map(s => s.count),
                    backgroundColor: data.stats.map(s => colores[s.tipo] || '#6c5ce7'),
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    } catch (error) {
        showToast('Error al cargar stats de mascota', 'error');
    }
}

// ==================== HELPERS ====================

function actualizarSelectores() {
    const opciones = mascotas.map(m => `<option value="${m.id}">${m.nombre}</option>`).join('');
    
    document.getElementById('emocion-mascota').innerHTML = 
        '<option value="">Selecciona mascota</option>' + opciones;
    
    document.getElementById('filtro-mascota').innerHTML = 
        '<option value="">Todas las mascotas</option>' + opciones;
}

function getNombreMascota(id) {
    const mascota = mascotas.find(m => m.id === id);
    return mascota ? mascota.nombre : 'Desconocida';
}

function getEmojiEspecie(especie) {
    const emojis = {
        perro: '🐕', gato: '🐈', ave: '🐦', conejo: '🐰',
        hamster: '🐹', pez: '🐟', reptil: '🦎', otro: '🐾'
    };
    return emojis[especie] || '🐾';
}

function getEmojiEmocion(tipo) {
    const emojis = {
        feliz: '😊', triste: '😢', ansioso: '😰', tranquilo: '😌',
        jugueton: '🎾', asustado: '😨', enfermizo: '🤒', cansado: '😴',
        excitado: '🤩', confundido: '😕'
    };
    return emojis[tipo] || '💭';
}

function getEmojiContexto(contexto) {
    const emojis = {
        comida: '🍖', paseo: '🚶', juego: '🎾', descanso: '😴',
        visita_veterinario: '🏥', socializacion: '🐕', sin_motivo_aparente: '❓'
    };
    return emojis[contexto] || '';
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
