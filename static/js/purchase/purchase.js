// static/js/purchase.js
document.addEventListener('DOMContentLoaded', () => new PurchaseManager());

class PurchaseManager {
  constructor() {
    this.d = document;
    this.detailPurchase = [];

    // --- Referencias DOM ---
    this.$supplier = this.d.getElementById("id_supplier");
    this.$payment = this.d.getElementById("id_payment_method");
    this.$product = this.d.getElementById("product");
    this.$btnAdd = this.d.getElementById("btnAdd");
    this.$form = this.d.getElementById("frmPurchase");
    this.$detailBody = this.d.getElementById("detalle");

    this.subtotalInput = this.d.getElementById("id_subtotal");
    this.ivaInput = this.d.getElementById("id_iva");
    this.totalInput = this.d.getElementById("id_total");

    // --- Inicialización ---
    if (this.$supplier) this.$supplier.selectedIndex = 0;
    if (this.$payment) this.$payment.selectedIndex = 0;

    // --- Eventos ---
    this.initEvents();

    // --- Si hay detalles previos ---
    if (typeof detail_purchases !== 'undefined' && detail_purchases.length > 0) {
      this.detailPurchase = detail_purchases.map(item => ({
        id: item.product,
        description: item.product__description,
        price: parseFloat(item.price),
        quantity: parseFloat(item.quantity),
        iva: parseFloat(item.iva),
        subtotal: parseFloat(item.subtotal)
      }));
      this.renderDetail();
      this.updateTotals();
    }
  }

  initEvents() {
    this.$product.addEventListener('change', e => this.onProductChange(e));
    this.$btnAdd.addEventListener('click', () => this.addProduct());
    this.$detailBody.addEventListener('click', e => this.removeProduct(e));
    this.$form.addEventListener('submit', e => this.submitForm(e));

    // Inicializa los valores
    this.onProductChange({ target: this.$product });
  }

  onProductChange(e) {
    const option = e.target.selectedOptions[0];
    if (!option) return;
    this.d.getElementById('price').value = option.dataset.price || 0;
    this.d.getElementById('iva').value = option.dataset.iva || 0;
  }

  addProduct() {
    const selected = this.$product.options[this.$product.selectedIndex];
    if (!selected.value) return alert("Seleccione un producto");

    const stock = parseInt(selected.dataset.stock || 0);
    const quantity = parseInt(this.d.getElementById('quantify').value);
    if (quantity <= 0 || quantity > stock) {
      return alert(`Cantidad inválida o mayor al stock disponible (${stock}).`);
    }

    const id = parseInt(selected.value);
    const description = selected.text;
    const price = parseFloat(selected.dataset.price);
    const iva = parseFloat(selected.dataset.iva);

    this.calculateProduct(id, description, iva, price, quantity);
  }

  calculateProduct(id, description, iva, price, quantity) {
    const existing = this.detailPurchase.find(p => p.id === id);
    if (existing && !confirm(`"${description}" ya está agregado. ¿Desea actualizar la cantidad?`)) return;

    if (existing) {
      quantity += existing.quantity;
      this.detailPurchase = this.detailPurchase.filter(p => p.id !== id);
    }

    const ivaValue = iva > 0 ? (price * quantity * (iva / 100)) : 0;
    const subtotal = price * quantity + ivaValue;

    this.detailPurchase.push({
      id,
      description,
      price,
      quantity,
      iva: ivaValue,
      subtotal
    });

    this.renderDetail();
    this.updateTotals();
  }

  renderDetail() {
    this.$detailBody.innerHTML = this.detailPurchase.map(prod => `
      <tr>
        <td>${prod.id}</td>
        <td>${prod.description}</td>
        <td>${prod.price.toFixed(2)}</td>
        <td>${prod.quantity}</td>
        <td>${prod.iva.toFixed(2)}</td>
        <td>${prod.subtotal.toFixed(2)}</td>
        <td class="text-center">
          <button class="text-danger" data-id="${prod.id}" rel="rel-delete">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>
    `).join('');
  }

  removeProduct(e) {
    const btn = e.target.closest('button[rel=rel-delete]');
    if (!btn) return;
    const id = parseInt(btn.dataset.id);
    this.detailPurchase = this.detailPurchase.filter(p => p.id !== id);
    this.renderDetail();
    this.updateTotals();
  }

  updateTotals() {
    const totals = this.detailPurchase.reduce((acc, p) => {
      acc.iva += p.iva;
      acc.subtotal += p.subtotal;
      return acc;
    }, { iva: 0, subtotal: 0 });

    this.subtotalInput.value = (totals.subtotal - totals.iva).toFixed(2);
    this.ivaInput.value = totals.iva.toFixed(2);
    this.totalInput.value = totals.subtotal.toFixed(2);
  }

  async submitForm(e) {
    e.preventDefault();
    if (parseFloat(this.totalInput.value) <= 0) {
      return alert("Debe agregar productos antes de guardar la compra.");
    }
    await this.savePurchase(save_url, purchase_list_url);
  }

  async savePurchase(urlPost, urlSuccess) {
    const formData = new FormData(this.$form);
    // Mapeo explícito para que los nombres coincidan con el backend
    const payload = this.detailPurchase.map(item => ({
      product: item.id,
      description: item.description,
      price: item.price,
      quantity: item.quantity,
      iva: item.iva,
      subtotal: item.subtotal
    }));
    formData.append("detail", JSON.stringify(payload));

    const csrf = this.d.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
      const res = await fetch(urlPost, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf
        },
        body: formData
      });

      if (!res.ok) throw new Error(`Error HTTP ${res.status}`);

      const result = await res.json();
      if (result.error) throw new Error(result.error);

      alert(result.msg);
      window.location.href = urlSuccess;
    } catch (err) {
      console.error("Error en guardado:", err);
      alert("Error al guardar la compra: " + err.message);
    }
  }
}
