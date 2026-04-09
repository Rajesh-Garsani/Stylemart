document.addEventListener('DOMContentLoaded', function() {


    const addToCartButtons = document.querySelectorAll('.add-to-cart-form .btn-cart, .btn-cart[data-id]');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const originalHTML = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check"></i> Added!';
            setTimeout(() => this.innerHTML = originalHTML, 1500);

        });
    });


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

    const filterSelects = document.querySelectorAll('.filter-group select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            console.log(`Filter changed: ${this.id} = ${this.value}`);
        });
    });

});
