(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        let firstChangeSelect = true;

        $('table.inline-related').on('change', 'tbody.djn-item .field-product select',  function (){
            if (!firstChangeSelect) {
                let row = $(this).parents('.form-row');
                ajaxUpdateSupplierPriceVariants($(this));
            } else {
                firstChangeSelect = false;
            }
        });


        function ajaxUpdateSupplierPriceVariants(productSelect) {
            let row =  productSelect.parents('.form-row');
            let select = row.find('.field-supplier_price_variants select');
            let initSelect = '<option value="" selected="">---------</option>'
            $.ajax({
                    type: "POST",
                    url: $('#ajaxUrls').data('getProductSuppliersPricesUrl'),
                    data: {'productId': productSelect.val()},
                    headers: {'X-CSRFToken': getCookie('csrftoken')},
                    success: function (response) {
                        console.log(response['supplier_prices_last_items']);
                        select.html(initSelect);
                        for (let spi of response['supplier_prices_last_items']){
                            select.children('option').last().after(`<option value="${spi['id']}">${spi['str_present']}</option>`);
                        }

                    }
                }, 200);
        }


        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    });
})(jQuery, undefined)






