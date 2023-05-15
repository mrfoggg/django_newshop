$(document).ready(function (){
    console.log('URL -', $('#ajaxUrls').data('ajaxPhoneFieldSearchUrl'));
    // $('#id_phone').select2();
    $('#id_incoming_phone, #id_phone').each(function (){
        let th = $(this);
        let thId = th.attr('id');
        th.select2({
            ajax: {
                url: $('#ajaxUrls').data('ajaxPhoneFieldSearchUrl'),
                dataType: 'json',
                processResults: function (data) {
                    let searchNumber = $('.select2-search__field').val().replace(/\D/g, "")
                    if (searchNumber.length===9){
                        setTimeout(function (){
                            console.log('this', th.prop(''));
                            $('#createNumber').html(
                                `<button style="width: 100%" type="button" class="btn btn-primary" onClick="ajaxAddNumber(${searchNumber}, \'${thId}\')">
                                   Сохранить новый номер
                            </button>`
                            ).find('button').focus();
                        },100)
                    }
                    return {results: data}
                }
            },
            placeholder: "номер для поиска или создания",
            allowClear: true,
            language: {
                noResults: function() {
                    return `<span id="createNumber" style="width: 100%">
                            <span>Введите весь номер для создания</span>
                        </span>
                </li>`;
                }
            },
            escapeMarkup: function (markup) {
                return markup;
            }
        }).on('select2:open', function (){
            $('.select2-search__field').mask("99  999-99-99",);
        }).next().css({width: '24rem',});
    })

});

function ajaxAddNumber(number, field_id) {
    const notification = new Notyf({
        duration: 4000,
        dismissible: true,
        position: {
            x: 'right',
            y: 'top'
        },
        types: [
            {
                type: 'error',
                className: 'success_notify',
                background: "#DE728E"
            }
        ]
    });
    console.log('field_id - ', field_id);
    let field = $(`#${field_id}`);
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('ajaxPhoneFieldAddUrl'),
        data: {phone_id: number},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            if (response['err']){
                console.log('НЕВЕРНЫЙ НОМЕР', notification);
                notification.error('Неверный номер');
            } else {
                let newOption = new Option(response['added_phone_str'], response['added_phone_id'], false, true);
                field.append(newOption).trigger('change').select2('close');
                console.log('FIELD - ', field);
            }
        }
    }, 200);
}



