(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        setTimeout(function () {
            $('table.inline-related').on('change', 'tbody.djn-item .field-product select',  function (){
                ajaxUpdateSupplierPriceVariants($(this));
            });

            $('table.inline-related').on('change', 'tbody.djn-item .field-price input, tbody.djn-item .field-supplier_price_variants select',  function (){
                let row = $(this).parents('.form-row');
                let price = row.find('.field-price input').val();
                let supplierPriceId = row.find('.field-supplier_price_variants select').val();
                ajaxUpdateFinanceCalculated(price, supplierPriceId, row);
            });
        }, 300)



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
                    select.html(initSelect);
                    for (let spi of response['supplier_prices_last_items']){
                        select.children('option').last().after(`<option value="${spi['id']}">${spi['str_present']}</option>`);
                    }
                    row.find('.field-full_current_price_info p').text(response['current_price']);
                    row.find('.field-price input').val('0.00');
                }
            }, 200);
        }

        function ajaxUpdateFinanceCalculated(price, supplierPriceId, row) {
            $.ajax({
                type: "POST",
                url: $('#ajaxUrls').data('ajaxGetCalculatedFinanceForPriceListUrl'),
                data: {'price': price, 'supplier_price_id': supplierPriceId},
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                success: function (response) {
                    row.find('.field-margin p').text(response['margin']);
                    row.find('.field-margin_percent p').text(response['margin_percent']);
                    row.find('.field-profitability p').text(response['profitability']);
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






