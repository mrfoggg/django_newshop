(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        $('.collapse_section').click(function (){
            $(this).parents('.admin_ajax_section').toggleClass('visible');
            $(this).toggleClass('visible').parent().next().slideToggle();
        });
    });
})(jQuery, undefined)



function ajaxUpdateSalePricesAndSupplierPriceVariants(row, productId, supplierOrderId=null, groupPriceType=null) {
    let priceVariantsSelect = row.find('.field-supplier_price_variants select');
    let initSelect = '<option value="" selected="">---------</option>'
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('getPriceAndProductSuppliersPricesUrl'),
        data: {'productId': productId, 'supplierOrderId': supplierOrderId, 'groupPriceType': groupPriceType},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            priceVariantsSelect.html(initSelect);
            for (let spi of response['supplier_prices_last_items']){
                priceVariantsSelect.children('option').last().after(`<option value="${spi['id']}">${spi['str_present']}</option>`);
            }
            row.find('.field-full_current_price_info p').text(response['current_price']);
            row.find('.field-sale_price input').val(response['current_price_amount']);
            if (response['supplier_prices_last_items'].length==1){
                priceVariantsSelect.children('option').last().prop('selected', true);
                priceVariantsSelect.trigger('change');
            } else {
                row.find('.field-margin p, .field-margin_percent p, .field-profitability p, .field-sale_total p, .field-margin_total p').text('-');
                row.find('.field-purchase_price input').val('0');
            }

        }
    }, 200);
}


function ajaxUpdateFinanceCalculated(row, price, supplierPriceId, quantity=null, purchasePrice=null) {
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('ajaxGetCalculatedFinanceForPriceListUrl'),
        data: {'price': price, 'supplier_price_id': supplierPriceId, 'quantity': quantity, 'purchase_price': purchasePrice},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            row.find('.field-margin p').text(response['margin']);
            row.find('.field-margin_percent p').text(response['margin_percent']);
            row.find('.field-profitability p').text(response['profitability']);
            if (quantity) {
                row.find('.field-sale_total p').text(response['sale_total']);
                row.find('.field-margin_total p').text(response['margin_total']);
                row.find('.field-purchase_total p').text(response['purchase_total']);
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