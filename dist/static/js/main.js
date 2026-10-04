/* Tokenly Main Utility Script */

document.addEventListener('DOMContentLoaded', function () {
    // Flash Alert Auto dismiss
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 4500);
    });
});

// Admin Modal Functions
window.openModal = function (modalId) {
    const el = document.getElementById(modalId);
    if (el) {
        el.classList.remove('hidden');
        el.classList.add('flex');
    }
};

window.closeModal = function (modalId) {
    const el = document.getElementById(modalId);
    if (el) {
        el.classList.add('hidden');
        el.classList.remove('flex');
    }
};

// Item Toggle Available AJAX
window.toggleItemAvailable = function (itemId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    fetch(`/admin/items/toggle/${itemId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const badge = document.getElementById(`avail-badge-${itemId}`);
            if (badge) {
                if (data.is_available) {
                    badge.className = 'px-2 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
                    badge.innerText = 'Available';
                } else {
                    badge.className = 'px-2 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30';
                    badge.innerText = 'Out of Stock';
                }
            }
        }
    });
};

// Reprint Receipt from History
window.reprintOrder = function (orderId) {
    fetch(`/history/reprint/${orderId}`)
    .then(r => r.json())
    .then(data => {
        if (data.success && data.receipt) {
            if (window.showReceiptModal) {
                window.showReceiptModal(data.receipt);
            }
        } else {
            alert('Unable to load receipt details.');
        }
    });
};
