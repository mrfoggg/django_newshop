(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        setTimeout(function () {
            $('table.inline-related').on('change', 'tbody.djn-item .field-product select',  function (){
                console.log('CHANGE field-product');
                ajaxUpdateSalePricesAndSupplierPriceVariants($(this));
            });

            $('table.inline-related').on('change', 'tbody.djn-item .field-price input, tbody.djn-item .field-supplier_price_variants select',  function (){
                let row = $(this).parents('.form-row');
                let price = row.find('.field-price input').val();
                let supplierPriceId = row.find('.field-supplier_price_variants select').val();
                ajaxUpdateFinanceCalculated(row, price, supplierPriceId);
            });
        }, 300)
    });
})(jQuery, undefined)
