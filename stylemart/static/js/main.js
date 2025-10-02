// static/js/main.js
// Updated client-side helpers for the Store (non-essential - server handles POSTs).
document.addEventListener('DOMContentLoaded', function() {

    // Graceful UI for add-to-cart forms (replace button text temporarily)
    const addToCartButtons = document.querySelectorAll('.add-to-cart-form .btn-cart, .btn-cart[data-id]');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // If button is inside a form, let form submit normally (no AJAX).
            // But update button text briefly to show feedback.
            const originalHTML = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check"></i> Added!';
            setTimeout(() => this.innerHTML = originalHTML, 1500);
            // Let form submit as normal (no preventDefault).
        });
    });

    // Quantity input quick +/- behavior (if you implement +/-).
    document.querySelectorAll('.quantity-btn.minus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.nextElementSibling;
            if (input && parseInt(input.value) > 1) {
                input.value = parseInt(input.value) - 1;
            }
        });
    });
    document.querySelectorAll('.quantity-btn.plus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;
            if (input) {
                input.value = parseInt(input.value) + 1;
            }
        });
    });

    // Simple console feedback for filter selects
    const filterSelects = document.querySelectorAll('.filter-group select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            console.log(`Filter changed: ${this.id} = ${this.value}`);
        });
    });

});
