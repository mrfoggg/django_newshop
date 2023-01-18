
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

        function moveLeftCursor(inp) {
            let pos = inp.selectionStart - 1;
            let val = $(inp).val();
            let leftChar = val.charAt(pos);
            let leftLeftChar = val.charAt(pos-1);
            let leftLeftLeftChar = val.charAt(pos-2);
            if (leftChar==='_' || leftChar===' ' && leftLeftChar===' ' || leftChar===' ' && leftLeftChar==='_' || leftChar==='-' && !/[0-9]/.test(leftLeftChar)) {
                $(inp).setCursorPosition(pos);
                moveLeftCursor(inp);
            }
        }

        $('#id_number_1').click(function(){
            if (!/[0-9]/.test($(this).val())) {
                $(this).setCursorPosition(0);
            } else if (this.selectionStart > 0) {
                moveLeftCursor(this);
            }
        });

        // $('#id_number_1').click(function (){
        //     if (!$(this).is(":focus")) {
        //         $(this).setCursorPosition(0);
        //     }
        // });

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

