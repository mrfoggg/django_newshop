(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        // задержка для того чтобы при загружке не срабатывали select change
        setTimeout(function () {
            $('table.inline-related').on('change', 'tbody.djn-item .field-product select, tbody.djn-item .field-supplier_order select', function (){
                let row = $(this).parents('.form-row');
                //при выборе товара или заказ поставшику обновить варинты закупочных цен. Если выбран и заказ опставщику то будет один вариант
                let thisFieldSection = $(this).parent().parent();
                ajaxUpdateSalePricesAndSupplierPriceVariants(
                    row,
                    row.find('.field-product select').val(),
                    row.find('.field-supplier_order select').val(),
                    thisFieldSection.hasClass('field-product')
                );
            });
            $('#id_group_price_type, #id_dropper').change(function (){
                $('table.inline-related tbody.djn-item').each(function (){
                    console.log('ROW - ', $(this));
                    ajaxUpdateSalePricesAndSupplierPriceVariants(
                        $(this), $(this).find('.field-product select').val(),
                        $(this).find('.field-supplier_order select').val(), true
                    );
                });

            });
            $('table.inline-related').on('change', 'tbody.djn-item .field-supplier_price_variants select', function (){
                // обновить закупочную цену в зависимости от выбраной установки цен поставщика
                console.log('change field-supplier_price_variants');
                ajaxUpdatePurchasePrice($(this));
            });

            $('table.inline-related').on('change', 'tbody.djn-item .field-sale_price input, tbody.djn-item .field-purchase_price input, tbody.djn-item .field-quantity input, tbody.djn-item .field-drop_price input', function (){
                let row = $(this).parents('.form-row');
                let price = row.find('.field-sale_price input').val();
                let supplierPriceId = row.find('.field-supplier_price_variants select').val();
                let quantity = row.find('.field-quantity input').val();
                let purchasePrice = row.find('.field-purchase_price input').val();
                let dropPrice = row.find('.field-drop_price input').val()==='-' ? 0 : row.find('.field-drop_price input').val();
                if (price&&(supplierPriceId||purchasePrice))
                    ajaxUpdateFinanceCalculated(row, price, supplierPriceId, quantity, purchasePrice, dropPrice);
            });

            $('#id_person').change(function (){
                $('select#id_contact_person, select#id_address').empty();
            });
        }, 700);
        let notSelectedOption = '<option value="" selected="">---------</option>';

        // в работе, проверить
        $('select#id_person, select#id_incoming_phone').on('change', function (){
            if ($(this).val()) {
                $('.field-dropper, .field-address').parent().slideDown();
                getPersonInfoAjax($('select#id_person').val(), true);
            } else {
                $('.field-dropper, .field-address').parent().slideUp();
            }
        });
        $('select#id_person').change(function () {
            getPersonPhones();
             $('#id_group_price_type').html(notSelectedOption);
        });

        // autoUpdateSelectActionButtons('#id_person, #id_incoming_phone, #id_address, #id_contact_person, #id_delivery_phone', 'person', '#id_person');

        getPersonPhones();
        $('#id_dropper').change(function (){
            getPersonInfoAjax($(this).val());
             $('#id_group_price_type').html(notSelectedOption);
        });

        $('#id_incoming_phone').change(getPersonsByPhone);
        $('#id_incoming_phone').trigger('change');
        $('#foundedPersons').on('click', 'button.select_person', function () {
            if (!$('#id_person').children(`option[value=${$(this).data('personId')}]`).length)
                $('#id_person').append(`<option value=${$(this).data('personId')}>${$(this).data('personName')}</option>`);
            $('#id_person').val($(this).data('personId')).trigger('change');
        });

        $('#id_incoming_phone, #id_person').change(buttonAddNumberShowOreHide);
        $('.flex-container.field-incoming_phone').on('click', 'button.ajax', buttonAddNumberShowOreHide);
        $('.person_phones_area').on('click', 'button.ajax', changePhoneParameters);
        buttonAddNumberShowOreHide();

        setTimeout(() => {
            $('.flex-container.fieldBox.field-incoming_phone .selection').append(`<p class="callContactPhone"><p id="foundContact"></p></p>`);
        },100);
    });
})(jQuery, undefined)

function copyTextButton(text){
    console.log(text);
    navigator.clipboard.writeText(text).then();
}

function changePhoneParameters(){
    let this_button = $(this);
    this_button.css('opacity', '.2');
    if (this_button.data('mode') == 'main_phone')
        $('.flex-container.field-person .select2-container').css('opacity', '.2');
    let start = +new Date();
    let personId = $('#id_person').val();
    let phoneId = $(this).parents('li').data('phoneId');
    let mode = $(this).data('mode');
    let action = $(this).hasClass('btn_yes') ? 'remove' : 'add';
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('changePhoneParameters'),
        data: {mode: mode, action: action, person_id: personId, phone_id: phoneId},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            getPersonsByPhone();
            setTimeout(function (){
                this_button.toggleClass('btn_yes').toggleClass('btn_no').children().first().toggleClass('icon_cross').toggleClass('icon_plus');
                this_button.css('opacity', '1');
                if (this_button.data('mode') == 'remove')
                    this_button.parents('li').remove();
                if (this_button.data('mode') == 'main_phone'){
                    $('.flex-container.field-person .select2-container').css('opacity', '1');
                    this_button.siblings('.remove_person_phone').toggle();
                }

                $('#select2-id_person-container').text(response.person_str);
                if (phoneId==$('#id_incoming_phone').val())
                    $('#id_incoming_phone').trigger('change');
                let otherPhoneButtons = $(`#personPhones .li_ajax:not([data-phone-id=${phoneId}])`).children('span.person_phone_ajax__buttons');
                if (mode=='main_phone' && action=='add') {
                    otherPhoneButtons.children('.main_phone').removeClass('btn_yes').addClass('btn_no').children().first().removeClass('icon_cross').addClass('icon_plus');
                    otherPhoneButtons.children('.remove_person_phone').show();
                }

                if (mode=='delivery_phone' && action=='add')
                    otherPhoneButtons.children('.delivery_phone').removeClass('btn_yes').addClass('btn_no').children().first().removeClass('icon_cross').addClass('icon_plus');
            },  (new Date() - start) > 200 ? 0 : 200 - (new Date() - start))
        }
    }, 200);
}


function getPersonsByPhone(){
    let ph_id = $('#id_incoming_phone').val();
    let start = +new Date();
    $('.founded_person_area').css('opacity', '.2');
    $('#foundedPersons').text('');
    if (ph_id) {
        // $('#change_id_incoming_phone').show().prop('href', $('#change_id_incoming_phone').data('hrefTemplate').replace('__fk__', $(this).val()));
        $.ajax({
            type: "POST",
            url: $('#ajaxUrls').data('getPersons'),
            data: {'phone_id': ph_id},
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            success: function (response) {
                for (let person of response['persons']){

                    let person_row = $.parseHTML(`<li class="li_ajax" >
                        <span class="person_ajax__info">
                            <span> <a href="${person.link}" target="_blank">${person.name}</a></span> 
                        </span>
                        <span class="person_ajax__buttons">
                            ${person.is_main_phone ? "<span class='admin_icon icon_home'></span>" : "" }
                            ${person.is_delivery_phone ? "<span class='admin_icon icon_delivery'></span>" : "" }
                            <button type='button' class='ajax my_admin_btn select_person' data-person-id="${person.id}" data-person-name="${person.name}">Выбрать контрагента</button>
                        </span>
                    </li>`);
                    $('#foundedPersons').append(person_row);
                    setTimeout(() => {$('.founded_person_area').css('opacity', '1');}, (new Date() - start) > 200 ? 0 : 200 - (new Date() - start));
                }
            }
        }, 200);
    } else {
        $('#change_id_incoming_phone').hide();
    }

}

// обрабатывается вьюхой button_add_number_to_person_ajax в order.view
function buttonAddNumberShowOreHide(){
        // $('#id_person').trigger('change');
    let phone_id = $('#id_incoming_phone').val();
    $('.callContactPhone').text('');
    if (phone_id) {
        $('#incomingPhoneButtons').show();
        let mode = $(this).data('mode') ? $(this).data('mode') : 'check'
        if (mode === 'check') {
            $('#incomingPhoneButtons').css('opacity', '.2');
        }

        let start = +new Date();
        let action = $(this).hasClass('btn_yes') ? 'remove' : 'add';

        $.ajax({
            type: "POST",
            url: $('#ajaxUrls').data('addPhoneToPerson'),
            data: {mode: mode ? mode : 'check', person_id: $('#id_person').val(), phone_id: phone_id, action: action},
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            success: function (response) {
                if (mode!='check')
                    $('#id_incoming_phone').trigger('change');
                    getPersonPhones();
                setTimeout(function (){
                    if (mode == 'check') {
                        $('#incomingPhoneButtons').remove();
                        $('.flex-container.field-incoming_phone').append($.parseHTML(`<div id="incomingPhoneButtons" class="admin_ajax_section admin_ajax_section__inline">
                            ${$('#id_person').val() ? "<button type='button' data-mode='add_to_person' class='ajax my_admin_btn add_to_person'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_person'></span></button>" : ''}
                            <button type='button' data-mode='viber' class='ajax my_admin_btn viber'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_viber'></span></button>
                            <button type='button' data-mode='telegram' class='ajax my_admin_btn telegram'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_telegram'></span></button>
                            <button type='button' data-mode='whatsapp' class='ajax my_admin_btn whatsapp'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_whatsapp'></span></button>
                            <button type='button' class='my_admin_btn copy_text_btn' onclick="copyTextButton(${response.number})"> <span class='admin_icon'></span></button>
                        </div>`));
                        $('#incomingPhoneButtons').children('.add_to_person').addClass(response.added ? 'btn_yes' : 'btn_no').children().first().addClass(response.added ? 'icon_cross' : 'icon_plus');
                        $('#incomingPhoneButtons').children('.viber').addClass(response.viber ? 'btn_yes' : 'btn_no').children().first().addClass(response.viber ? 'icon_cross' : 'icon_plus');
                        $('#incomingPhoneButtons').children('.telegram').addClass(response.telegram ? 'btn_yes' : 'btn_no').children().first().addClass(response.telegram ? 'icon_cross' : 'icon_plus');
                        $('#incomingPhoneButtons').children('.whatsapp').addClass(response.whats_up ? 'btn_yes' : 'btn_no').children().first().addClass(response.whats_up ? 'icon_cross' : 'icon_plus');
                        $('#incomingPhoneButton').css('opacity', '1');
                        // $('.flex-container.fieldBox.field-incoming_phone .selection').append(`<p class="callContactPhone">${response.chats_links}</p>`);
                        $('.callContactPhone').html(response.chats_links);
                        $('#foundContact').html(response.contact_person);
                    }

                },(new Date() - start) > 200 ? 0 : 200 - (new Date() - start));

            }
        }, 200);
    } else {
        $('#incomingPhoneButtons').hide();
    }
}


// 'root_app:ajax_updates_person_phones_info' mode='person_phones'
function getPersonPhones(){
    let p_id = $('select#id_person').val();
    if (p_id) {
        // $('.person_phones_area, #change_id_person, #delete_id_person').show();
        $('.person_phones_area').show();
    } else {
        // $('.person_phones_area, #change_id_person, #delete_id_person').hide();
        $('.person_phones_area').hide();
    }
    $('.person_phones_area').css('opacity', '.2');
    let start = +new Date();
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('personPhones'),
        data: {'person_id': p_id},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            $('#personPhones').text('');
            for (let pp of response['person_phones']) {
                let personPhoneRow =
                    $.parseHTML(`<li class="li_ajax" data-phone-id=${pp.phone_id}>
                        <span class="person_phone_ajax__info">
                            <span>${pp.link}</span> 
                            <span>${pp.chats_links}</span>
                        </span>
                        <span class="person_phone_ajax__buttons">
                             ${pp.main_number_av ? "<button type='button' data-mode='main_phone' class='ajax my_admin_btn main_phone'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_home'></span></button>" : ""}
                            <button type='button' data-mode='delivery_phone' class='ajax my_admin_btn delivery_phone'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_delivery'></span></button>
                            <button type='button' data-mode='remove' class='ajax my_admin_btn remove_person_phone'> <span class='admin_icon icon_small icon_cross'></span><span class='admin_icon icon_person'></span></button>
                            <button type='button' data-mode='viber' class='ajax my_admin_btn viber'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_viber'></span></button>
                            <button type='button' data-mode='telegram' class='ajax my_admin_btn telegram'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_telegram'></span></button>
                            <button type='button' data-mode='whatsapp' class='ajax my_admin_btn whatsapp'> <span class='admin_icon icon_small'></span><span class='admin_icon icon_whatsapp'></span></button>
                            <button type='button' class='my_admin_btn copy_text_btn' onclick="copyTextButton(${pp.number})"> <span class='admin_icon'></span></button>
                        </span>
                    </li>`);
                let buttons = $(personPhoneRow).children('span.person_phone_ajax__buttons');
                buttons.children('.main_phone').addClass(pp.is_main_number ? 'btn_yes' : 'btn_no').children().first().addClass(pp.is_main_number ? 'icon_cross' : 'icon_plus');
                buttons.children('.delivery_phone').addClass(pp.is_delivery_number ? 'btn_yes' : 'btn_no').children().first().addClass(pp.is_delivery_number ? 'icon_cross' : 'icon_plus');
                buttons.children('.viber').addClass(pp.viber ? 'btn_yes' : 'btn_no').children().first().addClass(pp.viber ? 'icon_cross' : 'icon_plus');
                buttons.children('.telegram').addClass(pp.telegram ? 'btn_yes' : 'btn_no').children().first().addClass(pp.telegram ? 'icon_cross' : 'icon_plus');
                buttons.children('.whatsapp').addClass(pp.whats_up ? 'btn_yes' : 'btn_no').children().first().addClass(pp.whats_up ? 'icon_cross' : 'icon_plus');
                if (pp.is_main_number) {
                    buttons.children('.remove_person_phone').hide();
                } else {
                    buttons.children('.remove_person_phone').show();
                }
                $('#personPhones').append(personPhoneRow);
            }
            setTimeout(function (){
                $('.person_phones_area').css('opacity', '1');
            }, (new Date() - start) > 200 ? 0 : 200 - (new Date() - start))
        }
    }, 200);
}


// провериь и установить доступность выбора дропера для заказов с этим контрагентом, обнвоить доступне оптовые цены
// для контрагента или указаного дропера
function getPersonInfoAjax(person_id, buyerMode=false) {
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('getPersonInfoAjaxUrl'),
        data: {'person_id': person_id},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            // let notSelectedOption = '<option value="" selected="">---------</option>';
            // $('#id_group_price_type').html(notSelectedOption);
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

