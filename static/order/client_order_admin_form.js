// import {ajaxUpdateSalePricesAndSupplierPriceVariants} from '/js_functions_for_admin.js'
(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        setTimeout(function () {
            $('table.inline-related').on('change', 'tbody.djn-item .field-product select', function (){
                ajaxUpdateSalePricesAndSupplierPriceVariants($(this));
            });
            $('table.inline-related').on('change', 'tbody.djn-item .field-supplier_price_variants select', function (){
                ajaxUpdateByPrice($(this));
            });
        }, 300)

    });
})(jQuery, undefined)


// обновить закупочную цену в зависимости от выбраной установки цен поставщика
function ajaxUpdateByPrice(select) {
    let row = select.parents('.form-row').find('.field-purchase_price input');
    console.log('ROW - ', row);
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('supplierPriceByPriceItemIdUrl'),
        data: {'price_item_id': select.val()},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            select.parents('.form-row').find('.field-purchase_price input').val(response['price']);
        }
    }, 200);
}





