(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        const checkboxes_is_main_foto = document.querySelectorAll(
            'div#inline-related_image td.field-is_main_1 input')
        const checkboxes_is_main_onfocus = document.querySelectorAll(
            'div#inline-related_image td.field-on_focus input')
        const checkboxes_is_hidden_foto = document.querySelectorAll(
            'div#inline-related_image td.field-is_hidden input')
        const checkboxes_foto_to_del = document.querySelectorAll(
            'div#inline-related_image td.delete input')

        mainFoto(checkboxes_is_main_foto, checkboxes_is_main_onfocus, checkboxes_foto_to_del, checkboxes_is_hidden_foto)
        mainFoto(checkboxes_is_main_onfocus, checkboxes_is_main_foto, checkboxes_foto_to_del, checkboxes_is_hidden_foto)
    })
        function mainFoto (fieldName, fieldNane_2, checkboxes_foto_to_del, checkboxes_is_hidden_foto) {
            for (let k=0; k < fieldName.length; k++) {
                if (fieldName[k].checked === true) {
                    checkboxes_foto_to_del[k].disabled = true
                    checkboxes_is_hidden_foto[k].disabled = true
                }
            }
            for (let i=0; i < fieldName.length; i++) {
                fieldName[i].onchange = function () {
                    if (this.checked === true) {
                        for(let j = 0; j < fieldName.length; j++){
                            if (j === i) {
                                checkboxes_foto_to_del[j].checked = false
                                checkboxes_foto_to_del[j].disabled = true
                                checkboxes_is_hidden_foto[j].checked=false
                                checkboxes_is_hidden_foto[j].disabled = true
                            } else {
                                fieldName[j].checked = false
                                if (fieldNane_2[j].checked === false) {
                                    checkboxes_foto_to_del[j].disabled = false
                                    checkboxes_is_hidden_foto[j].disabled = false
                                }
                            }
                        }
                    }
                }
            }
        }
})(jQuery, undefined)
