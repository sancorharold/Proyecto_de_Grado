// static/js/SaleManager.js
document.addEventListener('DOMContentLoaded', () => new SaleManager());

class SaleManager {
  constructor() {
    // --- Referencias DOM ---
    this.d = document;
    this.detailSale = [];

    this.$customer = this.d.getElementById("id_customer");
    this.$payment = this.d.getElementById("id_payment_method");
    this.$product = this.d.getElementById("product");
    this.$btnAdd = this.d.getElementById("btnAdd");
    this.$form = this.d.getElementById("frmSale");
    this.$detailBody = this.d.getElementById("detalle");

    this.subtotalInput = this.d.getElementById("id_subtotal");
    this.ivaInput = this.d.getElementById("id_iva");
    this.totalInput = this.d.getElementById("id_total");

    // --- Config inicial ---
    this.$customer.selectedIndex = 1;
    this.$payment.selectedIndex = 0;

    // --- Eventos ---
    this.initEvents();

    // --- Si hay detalles previos cargados ---
    if (typeof detail_sales !== 'undefined' && detail_sales.length > 0) {
      this.detailSale = detail_sales.map(item => ({
        id: item.product,
        description: item.product__description,
        price: parseFloat(item.price),
        quantify: parseFloat(item.quantity),
        iva: parseFloat(item.iva),
        sub: parseFloat(item.subtotal)
      }));
      this.renderDetail();
      this.updateTotals();
    }
  }

  // ---------------- Eventos ----------------
  initEvents() {
    this.$product.addEventListener('change', e => this.onProductChange(e));
    this.$btnAdd.addEventListener('click', () => this.addProduct());
    this.$detailBody.addEventListener('click', e => this.removeProduct(e));
    this.$form.addEventListener('submit', e => this.submitForm(e));

    // Llamar una vez para inicializar
    this.onProductChange({ target: this.$product });
  }

  // ---------------- Métodos principales ----------------
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
    const quantify = parseInt(this.d.getElementById('quantify').value);
    if (quantify <= 0 || quantify > stock) {
      return alert(`Cantidad inválida o mayor al stock disponible (${stock}).`);
    }

    const id = parseInt(selected.value);
    const description = selected.text;
    const price = parseFloat(selected.dataset.price);
    const iva = parseFloat(selected.dataset.iva);
    this.calculateProduct(id, description, iva, price, quantify);
  }

  calculateProduct(id, description, iva, price, quantify) {
    const existing = this.detailSale.find(p => p.id === id);
    if (existing && !confirm(`"${description}" ya está agregado. ¿Desea actualizar la cantidad?`)) return;

    if (existing) {
      quantify += existing.quantify;
      this.detailSale = this.detailSale.filter(p => p.id !== id);
    }

    const ivaValue = iva > 0 ? (price * quantify * (iva / 100)) : 0;
    let sub = price * quantify + ivaValue;
    this.detailSale.push({ id, description, price, quantify, iva: ivaValue, sub });
    this.renderDetail();
    this.updateTotals();
  }

  renderDetail() {
    this.$detailBody.innerHTML = this.detailSale.map(prod => `
      <tr>
        <td>${prod.id}</td>
        <td>${prod.description}</td>
        <td>${prod.price.toFixed(2)}</td>
        <td>${prod.quantify}</td>
        <td>${prod.iva.toFixed(2)}</td>
        <td>${prod.sub.toFixed(2)}</td>
        <td class="text-center">
          <button class="text-danger" data-id="${prod.id}" rel="rel-delete">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      </tr>`).join('');
  }

  removeProduct(e) {
    const btn = e.target.closest('button[rel=rel-delete]');
    if (!btn) return;
    const id = parseInt(btn.dataset.id);
    this.detailSale = this.detailSale.filter(p => p.id !== id);
    this.renderDetail();
    this.updateTotals();
  }

  updateTotals() {
    console.log(this.detailSale)
    const totals = this.detailSale.reduce((acc, p) => {
      acc.iva += p.iva;
      acc.sub += p.sub;
      return acc;
    }, { iva: 0, sub: 0 });

    this.subtotalInput.value = (totals.sub - totals.iva).toFixed(2);
    this.ivaInput.value = totals.iva.toFixed(2);
    this.totalInput.value = totals.sub.toFixed(2);
  }

  async submitForm(e) {
    e.preventDefault();
    if (parseFloat(this.totalInput.value) <= 0) {
      return alert("Debe agregar productos antes de guardar la venta.");
    }
    await this.saveSale(save_url, invoice_list_url);
  }

  async saveSale(urlPost, urlSuccess) {
    const formData = new FormData(this.$form);
    formData.append("detail", JSON.stringify(this.detailSale));

    const csrf = this.d.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
      const res = await fetch(urlPost, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf,
        },
        body: formData
      });

      if (!res.ok) throw new Error(`Error HTTP ${res.status}`);

      const result = await res.json();
      alert(result.msg);
      window.location.href = urlSuccess;
    } catch (err) {
      console.error("Error en guardado:", err);
      alert("Error al grabar la venta.");
      alert(result)
    }
  }
}
