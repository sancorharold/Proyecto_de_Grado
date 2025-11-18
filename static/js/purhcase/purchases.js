document.addEventListener('DOMContentLoaded', () => new PurchaseManager());

class PurchaseManager {
    constructor() {
        this.d = document;
        this.detailPurchase = [];

        // DOM
        this.$product = this.d.getElementById("product");
        this.$quantity = this.d.getElementById("quantity");
        this.$cost = this.d.getElementById("cost");
        this.$btnAdd = this.d.getElementById("btnAdd");
        this.$form = this.d.getElementById("frmPurchase");
        this.$detailBody = this.d.getElementById("purchase-details");

        this.subtotalInput = this.d.getElementById("id_subtotal");
        this.ivaInput = this.d.getElementById("id_iva");
        this.totalInput = this.d.getElementById("id_total");

        // Eventos
        this.initEvents();

        // Modo edición: cargar detalles existentes
        if (typeof detail_purchases !== "undefined" && detail_purchases.length > 0) {
            this.detailPurchase = detail_purchases.map(item => ({
                id: item.product,
                description: item.product__description,
                quantity: parseFloat(item.quantity),
                cost: parseFloat(item.cost),
                iva_percent: parseFloat(item.product__iva),
                subtotal: parseFloat(item.subtotal)
            }));

            this.renderDetail();
            this.updateTotals();
        }
    }

    // ------------------ EVENTOS ------------------
    initEvents() {
        this.$btnAdd.addEventListener('click', () => this.addProduct());
        this.$detailBody.addEventListener('click', e => this.removeProduct(e));
        this.$form.addEventListener('submit', e => this.submitForm(e));
    }

    // ------------------ AÑADIR PRODUCTO ------------------
    addProduct() {
        const selected = this.$product.options[this.$product.selectedIndex];
        if (!selected.value) return alert("Seleccione un producto");

        const quantity = parseFloat(this.$quantity.value);
        const cost = parseFloat(this.$cost.value);

        if (quantity <= 0 || cost < 0) {
            return alert("La cantidad y el costo deben ser válidos.");
        }

        const id = parseInt(selected.value);
        const description = selected.text;
        const iva_percent = parseFloat(selected.dataset.iva || 0);

        // Si ya existe → reemplazarlo
        this.detailPurchase = this.detailPurchase.filter(p => p.id !== id);

        const iva_amount = (cost * quantity) * (iva_percent / 100);
        const subtotal = (cost * quantity) + iva_amount;

        this.detailPurchase.push({
            id,
            description,
            quantity,
            cost,
            iva_percent,
            subtotal
        });

        this.renderDetail();
        this.updateTotals();
    }

    // ------------------ RENDER ------------------
    renderDetail() {
        this.$detailBody.innerHTML = this.detailPurchase.map(prod => `
            <tr>
                <td>${prod.description}</td>
                <td>${prod.quantity}</td>
                <td>${prod.cost.toFixed(2)}</td>
                <td>${prod.subtotal.toFixed(2)}</td>
                <td class="text-center">
                    <button type="button" class="btn btn-danger btn-sm"
                        data-id="${prod.id}" rel="rel-delete">X</button>
                </td>
            </tr>
        `).join('');
    }

    // ------------------ ELIMINAR PRODUCTO ------------------
    removeProduct(e) {
        const btn = e.target.closest('button[rel=rel-delete]');
        if (!btn) return;

        const id = parseInt(btn.dataset.id);
        this.detailPurchase = this.detailPurchase.filter(p => p.id !== id);

        this.renderDetail();
        this.updateTotals();
    }

    // ------------------ TOTALES ------------------
    updateTotals() {
        const totals = this.detailPurchase.reduce((acc, p) => {
            const item_subtotal = p.quantity * p.cost;
            const item_iva = item_subtotal * (p.iva_percent / 100);
            acc.subtotal += item_subtotal;
            acc.iva += item_iva;
            acc.total += p.subtotal;
            return acc;
        }, { subtotal: 0, iva: 0, total: 0 });

        this.subtotalInput.value = totals.subtotal.toFixed(2);
        this.ivaInput.value = totals.iva.toFixed(2);
        this.totalInput.value = totals.total.toFixed(2);
    }

    // ------------------ GUARDAR ------------------
    async submitForm(e) {
        e.preventDefault();

        if (this.detailPurchase.length === 0) {
            return alert("Debe agregar al menos un producto a la compra.");
        }

        const formData = new FormData(this.$form);
        formData.append("detail", JSON.stringify(this.detailPurchase));

        const csrf = this.d.querySelector("[name=csrfmiddlewaretoken]").value;

        try {
            const res = await fetch(save_url, {
                method: "POST",
                headers: { "X-CSRFToken": csrf },
                body: formData
            });

            const data = await res.json();

            alert(data.msg || data.error);
            if (data.url) window.location.href = data.url;

        } catch (err) {
            console.error("Error al guardar:", err);
            alert("Error en el servidor.");
        }
    }
}
