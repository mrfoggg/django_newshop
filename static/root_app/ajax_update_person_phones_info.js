let newMainPhoneId
let newDeliveryPhoneId
(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        $('table.inline-related').on('change', 'tbody.djn-item .field-phone select',  function (){
            ajaxUpdatePhoneInfo($(this));
        });

        $('#id_main_phone').on('change', function (){
            if ($('#personAjaxUrls').data('initUpdate')) {
                $('#personAjaxUrls').data('initUpdate', false);
            } else {
                newMainPhoneId =  parseInt($(this).val());
            }
        });

        $('#id_delivery_phone').on('change', function (){
            if ($('#personAjaxUrls').data('initUpdate')) {
                $('#personAjaxUrls').data('initUpdate', false);
            } else {
                newDeliveryPhoneId =  parseInt($(this).val());
            }
            console.log('DeliveryPhone CHAHGE');
        });

    });
})(jQuery, undefined)


function ajaxUpdatePhoneInfo(phoneSelect) {
    let row = phoneSelect.parents('.form-row');

    $.ajax({
        type: "POST",
        url: $('#personAjaxUrls').data('updatePhonesInfo'),
        data: {'person_id': $('.fieldBox.field-id div').text(), 'phone_id': phoneSelect.val()},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            row.find('.field-other_person_login_this_phone p').html(response['other_person_login']);
            row.find('.field-other_person_not_main').html(response['other_person_not_this_main']);
            row.find('.field-other_contacts').html(response['contacts']);
            let mainPhone = $('#id_main_phone');
            let deliveryPhone = $('#id_delivery_phone');
            let notSelectedOption = '<option value="" selected="">---------</option>'
            mainPhone.html(notSelectedOption);
            deliveryPhone.html(notSelectedOption);
            let allPhonesFields = $('#phones-group table.inline-related tbody.djn-item .field-phone select')
            for (let phone of allPhonesFields) {
                if (allPhonesFields.find(`option[value=${$(phone).val()}]:selected`).length > 1){
                    $(phone).next().css('border', '2px solid red');
                } else {
                    $(phone).next().css('border', 'none');
                }
                if (!deliveryPhone.children((`option[value=${$(phone).val()}]`)).length)
                    deliveryPhone.children().last().after(`<option value="${$(phone).val()}">${$(phone).children('option:selected').text()}</option>`);
                if ($(phone).parents('.form-row').find('.field-other_person_login_this_phone p').text()==='Отсутствуют') {
                    if (!mainPhone.children((`option[value=${$(phone).val()}]`)).length)
                        mainPhone.children().last().after(`<option value="${$(phone).val()}">${$(phone).children('option:selected').text()}</option>`);
                }
            }
            if (newMainPhoneId){
                mainPhone.val(newMainPhoneId);
            } else {
                mainPhone.val($('#personAjaxUrls').data('initMainPhoneId'));
            }
            if (newDeliveryPhoneId){
                deliveryPhone.val(newDeliveryPhoneId);
            } else {
                deliveryPhone.val($('#personAjaxUrls').data('initDeliveryPhoneId'));
            }

            console.log('DATA - ', $('#personAjaxUrls').data());

            console.log('=================');
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
