// import {ajaxUpdateSalePricesAndSupplierPriceVariants} from '/js_functions_for_admin.js'
(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        setTimeout(function () {
            $('table.inline-related').on('change', 'tbody.djn-item .field-product select, tbody.djn-item .field-supplier_order select', function (){
                let row = $(this).parents('.form-row');
                //при выборе товара или заказ поставшику обновить варинты закупочных цен. Если выбран и заказ опставщику то будет один вариант
                ajaxUpdateSalePricesAndSupplierPriceVariants(
                    row,
                    row.find('.field-product select').val(),
                    row.find('.field-supplier_order select').val()
                );
            });
            $('table.inline-related').on('change', 'tbody.djn-item .field-supplier_price_variants select', function (){
                // обновить закупочную цену в зависимости от выбраной установки цен поставщика
                ajaxUpdatePurchasePrice($(this));
            });

            $('table.inline-related').on('change', 'tbody.djn-item .field-sale_price input, tbody.djn-item .field-purchase_price input, tbody.djn-item .field-quantity input', function (){
                let row = $(this).parents('.form-row');
                let price = row.find('.field-sale_price input').val();
                let supplierPriceId = row.find('.field-supplier_price_variants select').val();
                let quantity = row.find('.field-quantity input').val();
                let purchasePrice = row.find('.field-purchase_price input').val();
                ajaxUpdateFinanceCalculated(row, price, supplierPriceId, quantity, purchasePrice);
            });
        }, 300)

    });
})(jQuery, undefined)


// обновить закупочную цену в зависимости от выбраной установки цен поставщика
function ajaxUpdatePurchasePrice(select) {
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('supplierPriceByPriceItemIdUrl'),
        data: {'price_item_id': select.val()},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            let purchasePrice = select.parents('.form-row').find('.field-purchase_price input');
            purchasePrice.val(response['price']);
            purchasePrice.trigger('change');
        }
    }, 200);
}

// обновить варианты закупочных цен в зависимости от выбраного заказа поставщику







