(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        $('#id_settlement').on('change', function (){
            console.log($(this).val());
            $('#id_address_type input').prop('disabled', 'disabled');
            $('#delivery_not_allowed_msg').remove();
            console.log('id_address_type input', $('#id_address_type input'));
            // console.log('id_address_type input',);
            $.ajax({
                type: "POST",
                url: 'http://127.0.0.1:8000/root_app/get_settlement_info/',
                data: {'settlement_ref': $(this).val()},
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                success: function (response) {
                    if (response['is_warehouses_exists']){
                        $('#id_address_type input[value="1"]').prop('disabled', false).parent().slideDown();
                    } else {
                        $('#id_address_type input[value="1"]').prop('disabled', false).parent().slideUp();
                    }
                    if (response['address_delivery_allowed']){
                        $('#id_address_type input[value="2"]').prop('disabled', false).parent().slideDown();
                    } else {
                        $('#id_address_type input[value="2"]').prop('disabled', false).parent().slideUp();
                    }
                    if (!response['is_warehouses_exists']&&!response['address_delivery_allowed'])
                        $('#id_address_type').after('<p id="delivery_not_allowed_msg">ДОСТАВКА НЕВОЗМОЖНА</p>')

                }
            }, 200)
        })

    })
})(jQuery, undefined)


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

