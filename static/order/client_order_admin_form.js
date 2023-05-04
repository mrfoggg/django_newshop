// if (!$) {
//     $ = django.jQuery;
// }
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
                if (price&&(supplierPriceId||purchasePrice))
                    ajaxUpdateFinanceCalculated(row, price, supplierPriceId, quantity, purchasePrice);
            });
            $('#id_person').change(function (){
                $('select#id_contact_person, select#id_address').empty();
            });
        }, 300)

        $('select#id_person').on('change', function (){
            getPersonInfoAjax($(this).val(), true);
            getPersonPhones($(this).val());
        });

        $('#id_dropper').change(function (){
            getPersonInfoAjax($(this).val());
        });

        $('#id_incoming_phone').change(function () {
            $('#foundedPersonsAndContacts').hide(100);
            getPersonsByPhone($(this).val());
        });

        $('#foundedPersons').on('click', 'button.select_person', function () {
            $('#id_person').val($(this).data('personId')).trigger('change');
            $('#foundedPersonsAndContacts').hide(100);
        });

    });
})(jQuery, undefined)

function getPersonsByPhone(ph_id){
    console.log('PHONE SELECT -', ph_id);
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('getPersons'),
        data: {'phone_id': ph_id},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            $('#foundedPersons').text('');
            for (let person of response['persons']){
                console.log(person);
                $('#foundedPersons').append(person);
            }
            $('#foundedPersonsAndContacts').show(400);
        }
    }, 200);
}

// 'root_app:ajax_updates_person_phones_info' mode='person_phones'
function getPersonPhones(p_id){
    console.log('PHONE getPersonPhones -', p_id);
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('personPhones'),
        data: {'person_id': p_id},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            $('#personPhones').text('');
            for (let pp of response['person_phones']) {
                $('#personPhones').append(
                    `<li>${pp[0]}</br>${pp[1]}</li>`
                );
            }
            console.log('person_phones -', response['person_phones']);
        }
    }, 200);
}


function getPersonInfoAjax(person_id, buyerMode=false) {
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('getPersonInfoAjaxUrl'),
        data: {'person_id': person_id},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            let notSelectedOption = '<option value="" selected="">---------</option>';
            $('#id_group_price_type').html(notSelectedOption);
            console.log('buyerMode - ', buyerMode);
            if (buyerMode) {

                $('#id_dropper').val('');
                if (response['dropper_available']) {
                    $('#id_dropper').prop('disabled', false);
                } else {
                    $('#id_dropper').val('').prop('disabled', true);
                }
            }
            for (let priceOption of response['group_price_types']) {
                $('#id_group_price_type').children('option').last().after(`<option value="${priceOption['id']}">${priceOption['name']}</option>`);
            }
            if (response['group_price_types'].length==1)
                $('#id_group_price_type').val(response['group_price_types'][0]['id']);
        }
    }, 200);
}
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







