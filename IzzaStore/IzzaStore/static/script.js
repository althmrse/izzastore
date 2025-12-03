let products = [
  { category: "Snacks", brand: "Piattos", quantity: 12, price: 20 },
  { category: "Drinks", brand: "Coke", quantity: 3, price: 15 },
  { category: "Canned Goods", brand: "555 Sardines", quantity: 0, price: 25 }
];

function viewProducts() {
  let html = `
    <table>
      <tr><th>Product</th><th>Category</th><th>Pieces</th></tr>
      ${products.map(p => `
        <tr>
          <td>${p.brand}</td>
          <td>${p.category}</td>
          <td>${p.quantity}</td>
        </tr>
      `).join('')}
    </table>
  `;
  document.getElementById('monitorOutput').innerHTML = html;
}

function lowStockAlert() {
  let low = products.filter(p => p.quantity < 5);
  let html = `
    <table>
      <tr><th>Product</th><th>Status</th><th>Pieces Left</th></tr>
      ${low.length ? low.map(p => `
        <tr>
          <td>${p.brand}</td>
          <td>${p.quantity === 0 ? "Out of Stock" : "Low Stock"}</td>
          <td>${p.quantity}</td>
        </tr>
      `).join('') : `<tr><td colspan="3">No low stock items.</td></tr>`}
    </table>
  `;
  document.getElementById('monitorOutput').innerHTML = html;
}

function dailySummary() {
  let totalItems = products.reduce((sum, p) => sum + p.quantity, 0);
  let totalValue = products.reduce((sum, p) => sum + (p.quantity * p.price), 0);

  let html = `
    <table>
      <tr><th>Metric</th><th>Value</th></tr>
      <tr><td>Total Items</td><td>${totalItems}</td></tr>
      <tr><td>Total Value</td><td>₱${totalValue.toFixed(2)}</td></tr>
    </table>
  `;
  document.getElementById('reportOutput').innerHTML = html;
}
