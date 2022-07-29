
(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        console.log($('#id_number_0').val())
        function setUkraineFormat() {
            if ($('#id_number_0').val()==='UA') {
                console.log(777)
                $('#id_number_1').prop('maxlength', '9').mask("99  999-99-99", {autoclear: false});
            } else {
                console.log(888)
                $('.field-phone input').prop('maxlength', '16').unmask()
            }
        }
        if ($('#id_number_0').val()==='') {
            console.log(11)
            $('#id_number_0').children('[value=UA]').prop('selected', true);
        }
        setUkraineFormat()
        $('#id_number_0').change(function (){
            setUkraineFormat()
        })
    })
})(jQuery, undefined)

