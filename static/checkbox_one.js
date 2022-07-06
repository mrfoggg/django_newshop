(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        const checkboxes_is_main_foto = document.querySelectorAll(
            'div#inline-related_image td.field-is_main_1 input')
        const checkboxes_is_main_onfocus = document.querySelectorAll(
            'div#inline-related_image td.field-on_focus input')
        const checkboxes_foto_to_del = document.querySelectorAll(
            'div#inline-related_image td.delete input')

        console.log(checkboxes_is_main_foto)
        console.log(checkboxes_is_main_foto.length )

        if (checkboxes_is_main_foto.length < 4) {
            for (let i=0; i < checkboxes_is_main_foto.length; i++) {
                checkboxes_is_main_foto[i].style.visibility = "hidden"
                checkboxes_is_main_onfocus[i].style.visibility = "hidden"
            }
        } else {
            mainFoto(checkboxes_is_main_foto, checkboxes_is_main_onfocus, checkboxes_foto_to_del, )
            mainFoto(checkboxes_is_main_onfocus, checkboxes_is_main_foto, checkboxes_foto_to_del, )
        }
    })
        function mainFoto (fieldName, fieldNane_2, checkboxes_foto_to_del) {
            for (let k=0; k < fieldName.length; k++) {
                if (fieldName[k].checked === true) {
                    checkboxes_foto_to_del[k].disabled = true
                }
            }
            for (let i=0; i < fieldName.length; i++) {
                fieldName[i].onchange = function () {
                    if (this.checked === true) {
                        for(let j = 0; j < fieldName.length; j++){
                            if (j === i) {
                                checkboxes_foto_to_del[j].checked = false
                                checkboxes_foto_to_del[j].disabled = true
                            } else {
                                fieldName[j].checked = false
                                if (fieldNane_2[j].checked === false) {
                                    checkboxes_foto_to_del[j].disabled = false
                                }
                            }
                        }
                    }
                }
            }
        }
})(jQuery, undefined)
