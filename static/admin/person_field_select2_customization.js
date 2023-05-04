$(document).ready(function (){
    let searchName;
    $('#id_person').select2({
        ajax: {
            url: $('#ajaxUrls').data('ajaxPersonFieldSearchUrl'),
            dataType: 'json',
            processResults: function (data) {
                searchName = $('.select2-search__field').val();
                // console.log('searchName', searchName.split(' ').map((s) => s.length>1));
                if (searchName.split(' ').length>1 && searchName.split(' ').every(value => value.length>1)){
                    setTimeout(function (){
                        $('#createPerson').html(
                            `<button style="width: 100%" type="button" class="btn btn-primary">
                                   Создать контрагента
                            </button>`
                        );
                    },100)
                }

                return {results: data}
            }
        },
        placeholder:  "контрагент для поиска или создания",
        allowClear: true,
        language: {
            noResults: function() {
                return `<span id="createPerson" style="width: 100%">
                            <span>Не найдено, введите полностью для создания</span>
                        </span>
                </li>`;
            }
        },
        escapeMarkup: function (markup) {
            return markup;
        }
    }).next().css({width: '24rem',});

    $('body').on('click', '#createPerson button', () => {
        ajaxAddPerson(searchName);
    });
});



function ajaxAddPerson(full_name) {
    console.log('full_name', full_name);
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('ajaxPersonFieldAddUrl'),
        data: {full_name: full_name},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            let newOption = new Option(response['added_person_str'], response['added_person_id'], false, true);
            $('#id_person').append(newOption).trigger('change').select2('close');
        }
    }, 200);
}


