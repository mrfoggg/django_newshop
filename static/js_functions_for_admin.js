function ajaxUpdateSalePricesAndSupplierPriceVariants(productSelect) {
    let row =  productSelect.parents('.form-row');
    let select = row.find('.field-supplier_price_variants select');
    let initSelect = '<option value="" selected="">---------</option>'
    $.ajax({
        type: "POST",
        url: $('#ajaxUrls').data('getPriceAndProductSuppliersPricesUrl'),
        data: {'productId': productSelect.val()},
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (response) {
            select.html(initSelect);
            for (let spi of response['supplier_prices_last_items']){
                select.children('option').last().after(`<option value="${spi['id']}">${spi['str_present']}</option>`);
            }
            row.find('.field-full_current_price_info p').text(response['current_price']);
            row.find('.field-price input').val('0.00');
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