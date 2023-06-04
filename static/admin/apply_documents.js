if (!$) {
    $ = django.jQuery;
}
Baton.Dispatcher.register('onReady', function () {
    $('.submit-row input[name="choose_date"]').click(function (e){
        $.datetimepicker.setLocale('ru');
        $('#datetimepicker').datetimepicker({
            inline: true,
            dayOfWeekStart: 1,
            maxDateTime: 0,
            format: "d/m/Y H:i"
        }).change(()=>{$('#activateSetDate').show()});
        console.log('CLICK');
        e.preventDefault();
        $('#selectDate').magnificPopup({
            type:'inline',
            midClick: true // Allow opening popup on middle mouse click. Always set it to true if you don't provide alternative source in href.
        });
        $('#selectDate').trigger('click');
    });
    $('#activateSetDate').click(() => {
        console.log('PPPRRR - ', $('#datetimepicker').val());
        $('#supplierorder_form').append(`<input type="text" name='apply_date' id="dateValue" style="display: none">`);
        $('#dateValue').val($('#datetimepicker').val());
        console.log('DATE - ', $('input[name="apply_date"]').prop('value'));
        $('#_activate_set_date').trigger('click');
    });
});







