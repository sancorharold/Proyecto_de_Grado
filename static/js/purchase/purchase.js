// static/js/purchase/purchase.js
document.addEventListener('DOMContentLoaded', () => new PurchaseManager());

class PurchaseManager {
    constructor() {
        this.d = document;
        this.detailPurchase = [];

        // --- DOM ---
        this.$supplier = this.d.getElementById("id_supplier");
        this.$numDocument = this.d.getElementById("id_num_document");
        this.$issueDate = this.d.getElementById("id_issue_date");
        this.$product = this.d.getElementById("product");
        this.$btnAdd = this.d.getElementById("btnAdd");
        this.$form = this.d.getElementById("frmPurchase");
        this.$detailBody = this.d.getElementById("detalle");

        this.subtotalInput = this.d.getElementById("id_subtotal");
        this.ivaInput = this.d.getElementById("id_iva");
        this.totalInput = this.d.getElementById("id_total");

        this.costInput = this.d.getElementById("cost");
        this.ivaProdInput = this.d.getElementById("ivaProd");
        this.quantifyInput = this.d.getElementById("quantify");

        // Evitar errores si algo no existe
        if (!this.$product || !this.costInput || !this.ivaProdInput) {
            console.error("Error: Faltan elementos del formulario en el HTML.");
            return;
        }

        this.initEvents();

        // --- Si hay detalles previos (modo editar) ---
        if (typeof detail_purchase !== "undefined" && Array.isArray(detail_purchase)) {
            this.detailPurchase = detail_purchase.map(item => ({
                product: item.product,
                description: item.product__description,
                price: parseFloat(item.price),
                quantity: parseFloat(item.quantity),
                iva: parseFloat(item.iva),
                sub: parseFloat(item.sub)
            }));
            this.renderDetail();
            this.updateTotals();
        }
    }

    initEvents() {
        this.$product.addEventListener("change", e => this.onProductChange(e));
        this.$btnAdd.addEventListener("click", () => this.addProduct());
        this.$detailBody.addEventListener("click", e => this.removeProduct(e));
        this.$form.addEventListener("submit", e => this.submitForm(e));

        // Solo actualizar si hay un producto seleccionado
        if (this.$product.selectedIndex > 0) {
            this.onProductChange({ target: this.$product });
        }
    }

    // --- Cambiar costo e IVA al seleccionar un producto ---
    onProductChange(e) {
        const option = e.target.selectedOptions ? e.target.selectedOptions[0] : null;
        if (!option) {
            this.costInput.value = "";
            this.ivaProdInput.value = "";
            return;
        }

        this.costInput.value = parseFloat(option.dataset.cost || 0).toFixed(2);
        this.ivaProdInput.value = parseFloat(option.dataset.iva || 0).toFixed(2);
    }

    // --- Agregar producto ---
    addProduct() {
        const selected = this.$product.options[this.$product.selectedIndex];
        if (!selected.value) return alert("Seleccione un producto.");

        const id = parseInt(selected.value);
        const description = selected.text;
        const price = parseFloat(selected.dataset.cost);
        const ivaPercent = parseFloat(selected.dataset.iva);
        let inputQuantity = document.getElementById("quantify");
        const quantity = parseFloat(inputQuantity.value || 1);
        
        if (quantity <= 0) return alert("La cantidad debe ser mayor a 0");

        const ivaValue = price * quantity * (ivaPercent / 100);
        const sub = price * quantity + ivaValue;

        // Si existe, actualizar
        const existing = this.detailPurchase.find(p => p.product === id);
        if (existing) {
            existing.quantity += quantity;
            existing.iva += ivaValue;
            existing.sub += sub;
        } else {
            this.detailPurchase.push({
                product: id,
                description,
                price,
                quantity,
                iva: ivaValue,
                sub
            });
        }

        this.renderDetail();
        this.updateTotals();
    }

    // --- Dibujar tabla ---
    renderDetail() {
        this.$detailBody.innerHTML = this.detailPurchase.map(p => `
            <tr>
                <td>${p.product}</td>
                <td>${p.description}</td>
                <td>${p.price.toFixed(2)}</td>
                <td>${p.quantity}</td>
                <td>${p.iva.toFixed(2)}</td>
                <td>${p.sub.toFixed(2)}</td>
                <td class="text-center">
                    <button type="button" class="text-danger" data-id="${p.product}" rel="rel-delete">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // --- Eliminar producto ---
    removeProduct(e) {
        const btn = e.target.closest("button[rel=rel-delete]");
        if (!btn) return;

        const id = parseInt(btn.dataset.id);
        this.detailPurchase = this.detailPurchase.filter(p => p.product !== id);

        this.renderDetail();
        this.updateTotals();
    }

    // --- Calcular totales ---
    updateTotals() {
        const totals = this.detailPurchase.reduce((acc, p) => {
            acc.iva += p.iva;
            acc.sub += p.sub;
            return acc;
        }, { iva: 0, sub: 0 });

        this.subtotalInput.value = (totals.sub - totals.iva).toFixed(2);
        this.ivaInput.value = totals.iva.toFixed(2);
        this.totalInput.value = totals.sub.toFixed(2);
    }

    // --- Guardar ---
    async submitForm(e) {
        e.preventDefault();
        if (this.detailPurchase.length === 0) return alert("Agregue al menos un producto");

        await this.savePurchase(save_url, purchase_list_url);
    }

    async savePurchase(urlPost, urlSuccess) {
        const detail = this.detailPurchase.map(p => ({
            id: p.product,
            description: p.description,
            price: p.price.toFixed(2),
            quantify: p.quantity,
            iva: p.iva.toFixed(2),
            sub: p.sub.toFixed(2)
        }));

        const formData = new FormData(this.$form);
        formData.append("detail", JSON.stringify(detail));

        const csrf = this.d.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const res = await fetch(urlPost, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": csrf
                },
                body: formData
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const result = await res.json();

            if (result.error) alert(result.error);
            else {
                alert(result.msg);
                window.location.href = urlSuccess;
            }
        } catch (err) {
            console.error("Error al guardar:", err);
            alert("Error al guardar la compra.");
        }
    }
}
