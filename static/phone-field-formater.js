
(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        //
        $.fn.setCursorPosition = function(pos) {
          if ($(this).get(0).setSelectionRange) {
            $(this).get(0).setSelectionRange(pos, pos);
          } else if ($(this).get(0).createTextRange) {
            var range = $(this).get(0).createTextRange();
            range.collapse(true);
            range.moveEnd('character', pos);
            range.moveStart('character', pos);
            range.select();
          }
        };
        $('#id_number_1').click(function (){
            if (!$(this).is(":focus")) {
                $(this).setCursorPosition(0);
            }
        })
        function setUkraineFormat() {
            console.log('setUkraineFormat');
            if ($('#id_number_0').val()==='UA') {

                $('#id_number_1').prop('maxlength', '9').mask("99  999-99-99", );
            } else {
                $('#id_number_1').prop('maxlength', '16').unmask();
            }
        }
        if ($('#id_number_0').val()==='') {
            $('#id_number_0').children('[value=UA]').prop('selected', true);
        }
        setUkraineFormat();
        $('#id_number_0').change(function (){
            setUkraineFormat()
        })
    })
})(jQuery, undefined)

