(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        setTimeout(function () {
            $('table.inline-related').on('change', 'tbody.djn-item .field-product select',  function (){
                ajaxUpdateSalePricesAndSupplierPriceVariants($(this));
            });

            $('table.inline-related').on('change', 'tbody.djn-item .field-price input, tbody.djn-item .field-supplier_price_variants select',  function (){
                let row = $(this).parents('.form-row');
                let price = row.find('.field-price input').val();
                let supplierPriceId = row.find('.field-supplier_price_variants select').val();
                ajaxUpdateFinanceCalculated(price, supplierPriceId, row);
            });
        }, 300)
    });
})(jQuery, undefined)


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

