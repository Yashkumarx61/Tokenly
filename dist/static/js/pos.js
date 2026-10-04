/* Tokenly POS Terminal - High Performance, Accessible & QA Optimized JS */

document.addEventListener('DOMContentLoaded', function () {
    let cart = [];
    let activeCategory = 'all';
    let searchQuery = '';
    let debounceTimer = null;

    // DOM Elements
    const cartItemsContainer = document.getElementById('cart-items-list');
    const emptyCartNotice = document.getElementById('empty-cart-notice');
    const subtotalEl = document.getElementById('cart-subtotal');
    const taxEl = document.getElementById('cart-tax');
    const grandTotalEl = document.getElementById('cart-grand-total');
    const itemCountBadge = document.getElementById('cart-count-badge');
    const checkoutBtn = document.getElementById('checkout-btn');
    const searchInput = document.getElementById('pos-search-input');
    const categoryPills = document.querySelectorAll('.category-pill');
    const discountInput = document.getElementById('cart-discount-input');

    // Debounced Search Filtering (PERF-01 Fix: Eliminates Main-Thread Stalls)
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            clearTimeout(debounceTimer);
            const val = e.target.value;
            debounceTimer = setTimeout(() => {
                searchQuery = val.toLowerCase().trim();
                filterMenuItems();
            }, 150);
        });
    }

    // Category Filter Pills Event Handler
    categoryPills.forEach(pill => {
        pill.addEventListener('click', function () {
            categoryPills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            activeCategory = this.dataset.category || 'all';
            filterMenuItems();
        });
    });

    function filterMenuItems() {
        const foodCards = document.querySelectorAll('.food-card-wrapper');
        let visibleCount = 0;

        foodCards.forEach(card => {
            const cardCat = card.dataset.category;
            const cardName = card.dataset.name.toLowerCase();
            const matchesCat = (activeCategory === 'all' || cardCat === activeCategory);
            const matchesSearch = (!searchQuery || cardName.includes(searchQuery));

            if (matchesCat && matchesSearch) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        const noItemsEl = document.getElementById('no-items-found');
        if (noItemsEl) {
            noItemsEl.style.display = (visibleCount === 0) ? 'block' : 'none';
        }
    }

    // Add To Cart Handlers
    window.handleAddToCart = function (btn) {
        if (!btn) return;
        const id = btn.dataset.id;
        const name = btn.dataset.name;
        const portion = btn.dataset.portion;
        const price = btn.dataset.price;
        window.addToCart(id, name, portion, price);
    };

    window.addToCart = function (id, name, portion, price) {
        id = parseInt(id, 10);
        price = parseFloat(price);

        if (isNaN(id) || isNaN(price) || price < 0) return;

        const existing = cart.find(item => item.id === id && item.portion === portion);

        if (existing) {
            existing.quantity += 1;
        } else {
            cart.push({
                id: id,
                name: name,
                portion: portion,
                price: price,
                quantity: 1
            });
        }

        renderCart();
        showToast(`Added 1x ${name} (${portion.toUpperCase()})`);
    };

    window.updateQty = function (id, portion, change) {
        const index = cart.findIndex(item => item.id === id && item.portion === portion);
        if (index > -1) {
            cart[index].quantity += change;
            if (cart[index].quantity <= 0) {
                cart.splice(index, 1);
            }
        }
        renderCart();
    };

    window.removeFromCart = function (id, portion) {
        cart = cart.filter(item => !(item.id === id && item.portion === portion));
        renderCart();
    };

    window.clearCart = function () {
        cart = [];
        renderCart();
    };

    if (discountInput) {
        discountInput.addEventListener('input', renderCart);
    }

    // Accessible & Precision-Safe Cart Rendering
    function renderCart() {
        if (!cartItemsContainer) return;

        cartItemsContainer.innerHTML = '';
        let subtotal = 0;
        let totalCount = 0;

        if (cart.length === 0) {
            if (emptyCartNotice) emptyCartNotice.style.display = 'flex';
            if (subtotalEl) subtotalEl.innerText = '₹0.00';
            if (grandTotalEl) grandTotalEl.innerText = '₹0.00';
            if (taxEl) taxEl.innerText = '₹0.00';
            if (itemCountBadge) itemCountBadge.innerText = '0';
            if (checkoutBtn) checkoutBtn.disabled = true;
            return;
        }

        if (emptyCartNotice) emptyCartNotice.style.display = 'none';
        if (checkoutBtn) checkoutBtn.disabled = false;

        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;
            totalCount += item.quantity;

            const row = document.createElement('div');
            row.className = 'flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-200 hover:border-slate-300 transition text-xs';
            
            const portionBadge = item.portion === 'half'
                ? '<span class="px-1.5 py-0.5 text-[9px] font-bold uppercase rounded bg-amber-100 text-amber-800 border border-amber-200 ml-1">Half</span>'
                : '<span class="px-1.5 py-0.5 text-[9px] font-bold uppercase rounded bg-emerald-100 text-emerald-800 border border-emerald-200 ml-1">Full</span>';

            row.innerHTML = `
                <div class="flex-1 min-w-0 pr-2">
                    <div class="flex items-center">
                        <span class="font-bold text-slate-900 truncate">${item.name}</span>
                        ${portionBadge}
                    </div>
                    <div class="text-[11px] font-mono text-slate-500 mt-0.5">₹${item.price.toFixed(2)} × ${item.quantity}</div>
                </div>
                <div class="flex items-center space-x-2">
                    <div class="flex items-center bg-white rounded-lg p-0.5 border border-slate-200 shadow-xs">
                        <button onclick="updateQty(${item.id}, '${item.portion}', -1)" aria-label="Decrease quantity of ${item.name}" class="w-5 h-5 flex items-center justify-center rounded text-slate-700 hover:bg-slate-100 font-bold text-xs">-</button>
                        <span class="w-5 text-center font-extrabold text-xs text-slate-900 font-mono" aria-live="polite">${item.quantity}</span>
                        <button onclick="updateQty(${item.id}, '${item.portion}', 1)" aria-label="Increase quantity of ${item.name}" class="w-5 h-5 flex items-center justify-center rounded text-slate-700 hover:bg-slate-100 font-bold text-xs">+</button>
                    </div>
                    <span class="font-mono font-extrabold text-xs text-slate-900 w-14 text-right">₹${itemTotal.toFixed(2)}</span>
                    <button onclick="removeFromCart(${item.id}, '${item.portion}')" aria-label="Remove ${item.name} from cart" class="text-slate-400 hover:text-red-600 p-1 transition font-bold">
                        ✕
                    </button>
                </div>
            `;
            cartItemsContainer.appendChild(row);
        });

        const rawDiscount = discountInput ? parseFloat(discountInput.value) : 0;
        const discountVal = isNaN(rawDiscount) ? 0 : Math.max(0, rawDiscount);
        const netSubtotal = Math.max(0, subtotal - discountVal);
        const taxVal = 0.0;
        const grandTotal = netSubtotal + taxVal;

        if (subtotalEl) subtotalEl.innerText = `₹${subtotal.toFixed(2)}`;
        if (taxEl) taxEl.innerText = `₹${taxVal.toFixed(2)}`;
        if (grandTotalEl) grandTotalEl.innerText = `₹${grandTotal.toFixed(2)}`;
        if (itemCountBadge) itemCountBadge.innerText = totalCount.toString();
    }

    // High Performance Generate Token & Bill Submit
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function () {
            if (cart.length === 0) return;

            const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value || 'cash';
            const rawDiscount = discountInput ? parseFloat(discountInput.value) : 0;
            const discountVal = isNaN(rawDiscount) ? 0 : Math.max(0, rawDiscount);
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

            checkoutBtn.disabled = true;
            checkoutBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg> Generating Token...
            `;

            fetch('/api/pos/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    items: cart.map(i => ({ item_id: i.id, portion: i.portion, quantity: i.quantity })),
                    payment_method: paymentMethod,
                    discount: discountVal
                })
            })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return res.json();
            })
            .then(data => {
                checkoutBtn.disabled = false;
                checkoutBtn.innerHTML = `
                    <svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path></svg>
                    Generate Token & Bill
                `;

                if (data.success) {
                    buildThermalPrintDOM(data.receipt);
                    window.print();
                    clearCart();
                    if (discountInput) discountInput.value = '';
                    showToast(`Token ${data.token_number} Generated! Ready for next order.`);
                } else {
                    alert('Checkout Error: ' + (data.error || 'Failed to process order'));
                }
            })
            .catch(err => {
                checkoutBtn.disabled = false;
                checkoutBtn.innerHTML = `Generate Token & Bill`;
                alert('Server connection error. Please try again.');
            });
        });
    }

    // Receipt Modal Handler
    window.showReceiptModal = function (receipt) {
        const modal = document.getElementById('receipt-modal');
        if (!modal) return;

        document.getElementById('rc-token-num').innerText = receipt.token_number;
        document.getElementById('rc-business-name').innerText = receipt.business_name;
        document.getElementById('rc-datetime').innerText = receipt.date_time;
        document.getElementById('rc-payment-mode').innerText = receipt.payment_method;
        document.getElementById('rc-subtotal').innerText = receipt.subtotal;
        document.getElementById('rc-discount').innerText = receipt.discount;
        document.getElementById('rc-grandtotal').innerText = receipt.grand_total;

        const itemsBody = document.getElementById('rc-items-list');
        itemsBody.innerHTML = '';
        receipt.items.forEach(item => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-dashed border-slate-700/60 text-xs';
            tr.innerHTML = `
                <td class="py-1.5 font-medium text-slate-200">
                    ${item.name} <span class="text-[10px] text-slate-400 font-mono">(${item.portion.toUpperCase()})</span>
                </td>
                <td class="py-1.5 text-center font-mono text-slate-300">x${item.quantity}</td>
                <td class="py-1.5 text-right font-mono text-slate-200">${item.total_price}</td>
            `;
            itemsBody.appendChild(tr);
        });

        buildThermalPrintDOM(receipt);
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    };

    window.closeReceiptModal = function () {
        const modal = document.getElementById('receipt-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    };

    window.triggerThermalPrint = function () {
        window.print();
    };

    function buildThermalPrintDOM(receipt) {
        let printContainer = document.getElementById('thermal-receipt-printable');
        if (!printContainer) {
            printContainer = document.createElement('div');
            printContainer.id = 'thermal-receipt-printable';
            document.body.appendChild(printContainer);
        }

        let itemRowsHTML = '';
        receipt.items.forEach(i => {
            itemRowsHTML += `
                <tr>
                    <td>${i.name} (${i.portion[0].toUpperCase()})</td>
                    <td style="text-align:center">x${i.quantity}</td>
                    <td style="text-align:right">${i.total_price}</td>
                </tr>
            `;
        });

        printContainer.innerHTML = `
            <div class="thermal-header">
                <div class="thermal-title">${receipt.business_name}</div>
                <div>${receipt.date_time}</div>
            </div>
            
            <div class="thermal-token-box">
                <div style="font-size:8pt; text-transform:uppercase;">ORDER TOKEN</div>
                <div class="thermal-token-num">${receipt.token_number}</div>
            </div>

            <table class="thermal-table">
                <thead>
                    <tr>
                        <th>ITEM</th>
                        <th style="text-align:center">QTY</th>
                        <th style="text-align:right">PRICE</th>
                    </tr>
                </thead>
                <tbody>
                    ${itemRowsHTML}
                </tbody>
            </table>

            <div class="thermal-divider"></div>

            <div style="display:flex; justify-content:space-between; font-size:10pt;">
                <span>Subtotal:</span>
                <span>${receipt.subtotal}</span>
            </div>
            
            <div class="thermal-total-row" style="margin-top:4px;">
                <span>TOTAL:</span>
                <span>${receipt.grand_total}</span>
            </div>
            
            <div style="font-size:9pt; margin-top:4px;">MODE: ${receipt.payment_method}</div>
            
            <div class="thermal-footer">
                <div>Thank you!</div>
                <div>TOKENLY POS</div>
            </div>
        `;
    }

    function showToast(msg) {
        let toast = document.getElementById('pos-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'pos-toast';
            toast.className = 'fixed bottom-20 right-4 bg-[#161f30] border border-[#1f2d44] text-white px-4 py-2.5 rounded-xl shadow-2xl text-xs font-semibold z-50 transition transform translate-y-4 opacity-0 pointer-events-none flex items-center space-x-2';
            document.body.appendChild(toast);
        }
        toast.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse"></span><span>${msg}</span>`;
        toast.classList.remove('translate-y-4', 'opacity-0', 'pointer-events-none');
        
        setTimeout(() => {
            toast.classList.add('translate-y-4', 'opacity-0', 'pointer-events-none');
        }, 3000);
    }
});
