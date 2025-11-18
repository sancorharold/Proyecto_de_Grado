// static/js/nomina/loan_manager.js

document.addEventListener('DOMContentLoaded', () => new LoanManager());

class LoanManager {
    constructor(params) {
        this.saveUrl = params.saveUrl;
        this.listUrl = params.listUrl;
        this.detailCuotas = params.initialDetail;
        this.$form = document.querySelector(params.formSelector);
        this.$detalleCuotasBody = document.querySelector(params.detailTableSelector);
        
        // Elementos del formulario
        this.$monto = this.$form.querySelector('#id_monto');
        this.$numCuotas = this.$form.querySelector('#id_numero_cuotas');
        this.$tipoPrestamo = this.$form.querySelector('#id_tipo_prestamo');
        this.$fechaPrestamo = this.$form.querySelector('#id_fecha_prestamo');

        // Elementos de visualización de totales
        this.$interesDisplay = document.querySelector('#interes_display');
        this.$montoPagarDisplay = document.querySelector('#monto_pagar_display');
        this.$saldoDisplay = document.querySelector('#saldo_display');

        // Elementos ocultos para envío a Django
        this.$interesHidden = this.$form.querySelector('#id_interes_hidden');
        this.$montoPagarHidden = this.$form.querySelector('#id_monto_pagar_hidden');
        this.$saldoHidden = this.$form.querySelector('#id_saldo_hidden');
    }

    /**
     * Obtiene la tasa de interés del atributo data-tasa del <option> seleccionado.
     * Debe existir en tu HTML.
     */
    getTasaInteres() {
        const selectedOption = this.$tipoPrestamo.options[this.$tipoPrestamo.selectedIndex];
        // Retorna el valor del atributo data-tasa, si no existe, usa 0
        return parseFloat(selectedOption.dataset.tasa) || 0;
    }

    /**
     * Formatea un número como moneda (ej: 1,234.56).
     */
    formatCurrency(value) {
        return value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    /**
     * Genera la tabla de amortización (cuotas).
     */
    generateCuotas() {
        const monto = parseFloat(this.$monto.value);
        const numCuotas = parseInt(this.$numCuotas.value);
        const tasaAnual = this.getTasaInteres() / 100;

        if (isNaN(monto) || monto <= 0) {
            return alert("Ingrese un Monto Solicitado válido.");
        }
        if (isNaN(numCuotas) || numCuotas <= 0) {
            return alert("Ingrese un Número de Cuotas válido.");
        }
        if (isNaN(tasaAnual) || tasaAnual < 0) {
            return alert("Tipo de Préstamo no tiene una tasa de interés válida (data-tasa).");
        }
        if (!this.$fechaPrestamo.value) {
            return alert("Seleccione una Fecha de Préstamo.");
        }

        const tasaMensual = tasaAnual / 12;
        let montoInteres = 0;
        let cuotaFija = 0;
        
        // CÁLCULO DE CUOTA FIJA (Método francés o cuota constante)
        if (tasaMensual > 0) {
            // Fórmula de pago (PMT) simplificada
            cuotaFija = monto * tasaMensual / (1 - Math.pow(1 + tasaMensual, -numCuotas));
        } else {
            // Sin interés
            cuotaFija = monto / numCuotas;
        }

        let saldoPendiente = monto;
        this.detailCuotas = [];
        
        // Parseo de la fecha (crucial para evitar problemas de zona horaria)
        const fechaInicio = new Date(this.$fechaPrestamo.value + 'T00:00:00');
        
        // Si el mes de inicio es 12 (diciembre), el constructor lo convierte a enero del siguiente año,
        // por eso usamos la fecha de inicio del input como base para el primer vencimiento.
        let baseDate = new Date(fechaInicio.getFullYear(), fechaInicio.getMonth(), fechaInicio.getDate());

        for (let i = 1; i <= numCuotas; i++) {
            
            // Calculamos el vencimiento: sumamos 'i' meses a la fecha base.
            // La fecha de vencimiento es el mismo día del mes siguiente (i=1), y así sucesivamente.
            const vencimiento = new Date(baseDate.getFullYear(), baseDate.getMonth() + i, baseDate.getDate());
            
            // Si el día original es 31 y el nuevo mes no lo tiene, Date() ajusta al último día de ese mes.
            
            // --- Cálculo de amortización simple para determinar interés total ---
            // Asumiendo que la cuota es igual al valor total a pagar por cuota (principal + interés).
            
            const valorCuota = cuotaFija;
            
            // En un sistema simple, solo usamos la cuota fija para el total a pagar en el detalle.
            // Si queremos el interés real, se requiere un cálculo más complejo de amortización por cuota.
            
            // Acumulamos el interés total si lo necesitamos
            // La amortización simple asume que la cuota fija ya incluye el interés.
            // Para fines de este cálculo: MontoTotalPagar = CuotaFija * NumCuotas.
            
            
            // Actualización del saldo pendiente (solo para mostrar)
            saldoPendiente -= cuotaFija;

            this.detailCuotas.push({
                numero_cuota: i,
                // Formatear a YYYY-MM-DD para Django (Ej: 2025-11-01)
                fecha_vencimiento: vencimiento.toISOString().substring(0, 10), 
                valor_cuota: parseFloat(valorCuota.toFixed(2)),
                // El saldo de la cuota al crear es su valor total (hasta que se pague)
                saldo_cuota: parseFloat(valorCuota.toFixed(2)), 
                // saldo_restante_prestamo: Math.max(0, parseFloat(saldoPendiente.toFixed(2)))
            });
        }
        
        // Calcular totales finales (Interés y Monto a Pagar)
        const montoTotalPagar = this.detailCuotas.reduce((sum, item) => sum + item.valor_cuota, 0);
        const interesTotal = montoTotalPagar - monto;

        // Actualizar displays
        this.$interesDisplay.textContent = `$${this.formatCurrency(interesTotal)}`;
        this.$montoPagarDisplay.textContent = `$${this.formatCurrency(montoTotalPagar)}`;
        this.$saldoDisplay.textContent = `$${this.formatCurrency(montoTotalPagar)}`; // Inicialmente, el saldo es el monto a pagar

        // Actualizar campos ocultos (para enviar a Django)
        this.$interesHidden.value = interesTotal.toFixed(2);
        this.$montoPagarHidden.value = montoTotalPagar.toFixed(2);
        this.$saldoHidden.value = montoTotalPagar.toFixed(2);

        this.renderDetail();
        alert("Cuotas generadas con éxito. Revise la tabla.");
    }

    /**
     * Renderiza las cuotas en la tabla.
     */
    renderDetail() {
        if (!this.$detalleCuotasBody) return;
        
        let html = '';
        this.detailCuotas.forEach((item, index) => {
            html += `
                <tr>
                    <td>${item.numero_cuota}</td>
                    <td>${item.fecha_vencimiento}</td>
                    <td>$${this.formatCurrency(item.valor_cuota)}</td>
                    <td>$${this.formatCurrency(item.saldo_cuota)}</td>
                    <td>
                        <button type="button" class="btn btn-sm btn-danger" onclick="loanManagerInstance.removeCuota(${index})">
                            ❌
                        </button>
                    </td>
                </tr>
            `;
        });
        this.$detalleCuotasBody.innerHTML = html;
    }
    
    /**
     * Elimina una cuota del detalle (solo si se necesita editar manualmente).
     */
    removeCuota(index) {
        this.detailCuotas.splice(index, 1);
        this.renderDetail();
        // Nota: Al eliminar, deberías recalcular los totales de cabecera si es permitido.
    }

    /**
     * Envía el formulario por AJAX a Django.
     */
    async savePrestamo() {
        if (this.detailCuotas.length === 0) {
            alert("Debe generar las cuotas antes de guardar el préstamo.");
            return;
        }

        const formData = new FormData(this.$form);
        
        // 🚨 CRUCIAL: Serializa y adjunta el detalle de cuotas como JSON 🚨
        formData.append("detail", JSON.stringify(this.detailCuotas));
        
        try {
            const response = await fetch(this.saveUrl, {
                method: 'POST',
                body: formData,
                // No se necesita el Content-Type si se usa FormData sin JSON.stringify
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.msg);
                window.location.href = this.listUrl;
            } else {
                // Manejar errores de Django (validación de form_valid o excepciones)
                alert(`Error al guardar: ${data.error || 'Ocurrió un error desconocido.'}`);
            }
        } catch (error) {
            console.error('Error en la petición AJAX:', error);
            alert("Error de conexión al guardar el préstamo.");
        }
    }
}

// Inicialización global para usar el removeCuota en el onclick
let loanManagerInstance;

document.addEventListener('DOMContentLoaded', () => {
    const LOAN_MANAGER_PARAMS = {
        saveUrl: document.querySelector('#frmPrestamo').dataset.saveUrl, // Necesitas setear este data-attribute
        listUrl: "{% url 'nomina:prestamo_list' %}", // Reemplaza esto con una forma dinámica si es necesario
        initialDetail: JSON.parse(document.querySelector('#frmPrestamo').dataset.initialDetail || '[]'),
        formSelector: "#frmPrestamo",
        detailTableSelector: "#detalle_cuotas",
    };
    
    loanManagerInstance = new LoanManager(LOAN_MANAGER_PARAMS);
    
    // Asignar eventos (usando el objeto inicializado)
    document.getElementById('btnGenerateCuotas').addEventListener('click', () => {
        loanManagerInstance.generateCuotas();
    });

    document.getElementById('frmPrestamo').addEventListener('submit', function(e) {
        e.preventDefault();
        loanManagerInstance.savePrestamo();
    });
    
    // Si hay detalles iniciales (edición), renderizarlos al cargar la página
    if (loanManagerInstance.detailCuotas.length > 0) {
        loanManagerInstance.renderDetail();
    }
});