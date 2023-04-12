(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {

        $('.field-product select, .field-sale_price input, .field-quantity input').change(function (){
            let row = $(this).parents('.form-row');
            // console.log(row.children('.field-sale_price').children('input').val());
            if (row.children('.field-sale_price').children('input').val())
                ajaxUpdateRowFinance(row)
        })


        function ajaxUpdateRowFinance(row) {
            console.log(row);
            $.ajax({
                    type: "POST",
                    url: $('#ajaxUrls').data('pricesAjaxUrl'),
                    data: {},
                    headers: {'X-CSRFToken': getCookie('csrftoken')},
                    success: function (response) {
                        console.log(response);
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
    });
})(jQuery, undefined)






