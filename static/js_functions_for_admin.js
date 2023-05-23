(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        $('.collapse_section').click(function (){
            $(this).parents('.admin_ajax_section').toggleClass('visible');
            $(this).toggleClass('visible').parent().next().slideToggle();
        });
        console.log('JS_FUNCTIONS_FOR_ADMIN');
        autoUpdateSelectActionButtons('#id_person, #id_incoming_phone, #id_address, #id_contact_person, #id_delivery_phone, #id_phone', 'person', '#id_person');
    });
})(jQuery, undefined)


function autoUpdateSelectActionButtons(selector, initFieldName=null, outerFieldSelector=null) {
    $(selector).change(function (){
        let element_id = $(this).prop('id');
        let editButton = $(`#change_${element_id}`);
        let delButton = $(`#delete_${element_id}`);
        let viewButton = $(`#view_${element_id}`);
        let value = $(this).val();
        if (value) {
            editButton.add(delButton).add(viewButton).show();
            if (editButton.length)
                editButton.prop('href', editButton.data('hrefTemplate').replace('__fk__', value));
            if (delButton.length)
                delButton.prop('href', delButton.data('hrefTemplate').replace('__fk__', value));
            if (viewButton.length)
                viewButton.prop('href', viewButton.data('hrefTemplate').replace('__fk__', value));
        } else {
            editButton.add(delButton).add(viewButton).hide();
        }
    });
    function updateAddButtons() {
        $(selector).each(function (){
            let element_id = $(this).prop('id');
            let addButton = $(`#add_${element_id}`);
            addButton.prop('href', addButton.prop('href') + `&${initFieldName}=${$(outerFieldSelector).val()}`);
        });
    }
    if (initFieldName){
        updateAddButtons();
        $(outerFieldSelector).change(function (){
            updateAddButtons();
        });
    }
}


// finance.view ajax_get_product_price_and_suppliers_prices_variants
function ajaxUpdateSalePricesAndSupplierPriceVariants(row, productId, supplierOrderId=null, updateSalePrices) {
    let priceVariantsSelect = row.find('.field-supplier_price_variants select');
    let initSelect = '<option value="" selected="">---------</option>'
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('getPriceAndProductSuppliersPricesUrl'),
        data: {
            productId: productId, supplierOrderId: supplierOrderId, groupPriceId: $('#id_group_price_type').val(),
            // dropperId: $('#id_dropper').val()
        },
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            priceVariantsSelect.html(initSelect);
            for (let spi of response['supplier_prices_last_items']){
                priceVariantsSelect.children('option').last().after(`<option value="${spi['id']}">${spi['str_present']}</option>`);
            }
            if (updateSalePrices) {
                if (!$('#id_dropper').val() && response['group_price_val']) {
                    row.find('.field-sale_price input').val(response['group_price_val']);
                } else {
                    row.find('.field-sale_price input').val(response['current_price_amount']);
                }
            }

            row.find('.field-full_current_price_info p').text(response['current_price']);
            row.find('.field-current_group_price p').text(response['group_price_info']);
            if ($('#id_dropper').val()) {
                row.find('.field-drop_price input').val(response['group_price_val']).prop( "disabled", false );
            } else {
                row.find('.field-drop_price input').val('-').prop( "disabled", true );
            }

            if (response['supplier_prices_last_items'].length===1){
                priceVariantsSelect.children('option').last().prop('selected', true);
                priceVariantsSelect.trigger('change');
            } else {
                row.find('.field-margin p, .field-margin_percent p, .field-profitability p, .field-sale_total p, .field-margin_total p').text('-');
                row.find('.field-purchase_price input').val('0');
            }

        }
    }, 200);
}


function ajaxUpdateFinanceCalculated(row, price, supplierPriceId, quantity=null, purchasePrice=null, dropPrice) {
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('ajaxGetCalculatedFinanceForPriceListUrl'),
        data: {price: price, supplier_price_id: supplierPriceId, quantity: quantity,
            purchase_price: purchasePrice, drop_price: dropPrice},
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