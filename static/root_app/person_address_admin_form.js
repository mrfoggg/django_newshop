(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        actionsWhenSettlementSet($('#id_settlement').val(), true);

        $('#id_settlement').on('change', function (){
            $('#delivery_not_allowed_msg').remove();
            actionsWhenSettlementSet($(this).val(), false);
        });
        // $('#id_settlement').prop('disabled', 'disabled');

        $('input[name="address_type"]').on('change', function (){
            showOrHideAddressFields($(this).val());
        });
        $('input[name="address_type"]').click(function (){
            $('.field-address_type').data('isFieldSetAuto', false);
        })
    })
})(jQuery, undefined)

function showOrHideAddressFields(deliveryType){
    console.log('deliveryType - ', deliveryType)
    const addressDeliveryFields = $('.field-city, .field-street, .field-build, .field-comment');
    if (deliveryType==1){
        $('.field-warehouse').show();
        addressDeliveryFields.hide();
    } else if (deliveryType==2) {
        $('.field-warehouse').hide();
        addressDeliveryFields.show();
    } else {
        $('.field-warehouse').hide();
        addressDeliveryFields.hide();
    }
}

function actionsWhenSettlementSet(settlement, onLoad){
    const addressDeliveryFields = $('.field-city, .field-street, .field-build, .field-comment');
    if (settlement){
        $('.field-address_type').show();
        //перед началом запроса сдеалть форму полупрозрачной
        $('#personaddress_form').css('opacity', '30%');
        $.ajax({
            type: "POST",
            url: 'http://127.0.0.1:8000/root_app/get_settlement_info/',
            data: {'settlement_ref': settlement},
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            success: function (response) {
                //показать или скрыть необходимы варианты типов адреса
                if (response['is_warehouses_exists']){
                    $('#id_address_type input[value="1"]').parent().show();
                } else {
                    $('#id_address_type input[value="1"]').parent().hide();
                }
                if (response['address_delivery_allowed']){
                    $('#id_address_type input[value="2"]').parent().show();
                    $('.field-city .readonly').html(response['city']);

                    //скрытый select который испольщзется для работы фильтрации поля с улицами по ref города этого поля
                    let cityInputHtml =
                    `<div style="display: none"> 
                        <label for="id_city">Город Новой почты откуда производится адресная доставка:</label>
                        <div class="related-widget-wrapper" data-model-ref="Город новой почты">
                            <select name="city" id="id_city">
                                <option value="${response['city_ref']}" selected></option>
                            </select>
            
                               <a class="related-widget-wrapper-link view-related" id="view_id_city" data-href-template="/admin/nova_poshta/city/__fk__/change/?_to_field=ref" href="/admin/nova_poshta/city/db5c8980-391c-11dd-90d9-001a92567626/change/?_to_field=ref" aria-label="View selected Город новой почты"><img src="/static/admin/img/icon-viewlink.svg" alt="Переглянути"></a>
                        </div>
                    </div>`
                    $('.field-city .readonly').append(cityInputHtml);
                    if (!onLoad)
                        $('#id_street').val(null).trigger('change');
                } else {
                    $('#id_address_type input[value="2"]').parent().hide();
                }
                // если нет доступных вариантов доставки
                if (!response['is_warehouses_exists']&&!response['address_delivery_allowed']){
                    $('.field-address_type').show();
                    $('#id_address_type').after('<p id="delivery_not_allowed_msg">НЕТ ДОСТУПНЫХ ВАРИАНТОВ ДОСТАВКИ</p>');
                    $('.field-warehouse').hide();
                    addressDeliveryFields.hide();
                    $('input[name="address_type"]').prop('checked', false);
                }

                setTimeout(function (){
                    // вернуть в норму прозрачность всей формы
                    $('#personaddress_form').css('opacity', '100%');
                    //если эта функция вызвана не при загрузке страницы то выбрать первый доступный тип доставки
                    if (!onLoad){
                        let deliveryTypeToSet = $('#id_address_type input:visible').first();
                        deliveryTypeToSet.prop('checked', true);
                        showOrHideAddressFields(deliveryTypeToSet.val());
                    }
                    else {
                        showOrHideAddressFields($('input[name="address_type"]:checked').val());
                    }
                }, 450)
            }
        }, 200);
    } else {
        $('.field-address_type').hide();
        $('.field-warehouse').hide();
        addressDeliveryFields.hide();
    }
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

