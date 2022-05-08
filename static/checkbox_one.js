(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        const checkboxes_is_main_foto = document.querySelectorAll(
            'div#inline-related_image td.field-is_main_1 input')
        const checkboxes_is_main_onfocus = document.querySelectorAll(
            'div#inline-related_image td.field-on_focus input')
        const checkboxes_is_active_foto = document.querySelectorAll(
            'div#inline-related_image td.field-is_active input')
        const checkboxes_foto_to_del = document.querySelectorAll(
            'div#inline-related_image td.delete input')

        mainFoto(checkboxes_is_main_foto, checkboxes_foto_to_del, checkboxes_is_active_foto)
        mainFoto(checkboxes_is_main_onfocus, checkboxes_foto_to_del, checkboxes_is_active_foto)
    })
        function mainFoto (fieldName, checkboxes_foto_to_del, checkboxes_is_active_foto) {
            for (let i=0; i < fieldName.length; i++) {
                fieldName[i].onchange = function () {
                    if (this.checked === true) {
                        for(let j = 0; j < fieldName.length; j++){
                            if (j == i) {
                                checkboxes_foto_to_del[j].checked = false
                                checkboxes_foto_to_del[j].disabled = true
                                checkboxes_is_active_foto[j].checked=true
                            } else {
                                fieldName[j].checked = false
                                checkboxes_foto_to_del[j].disabled = false
                            }
                        }
                    }
                }
            }
        }
})(jQuery, undefined)
