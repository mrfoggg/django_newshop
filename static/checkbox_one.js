(function ($, undefined) {
    // init listeners
    Baton.Dispatcher.register('onReady', function () {
        const checkboxes_is_main_foto = document.querySelectorAll('td.field-is_main_1 input')
        console.log('ЧЕКБОКСЫ')

        checkboxes_is_main_foto.forEach(elem => {
            elem.onchange = function () {
                if (this.checked==true) {
                     checkboxes_is_main_foto.forEach(el =>{
                        if (el!=elem) {
                            el.checked = false
                        }
                    })
                }
            }
        })

        // document.querySelector('td.field-is_main_1 input').setAttribute('checked', '')
        // document.querySelector('td.field-is_main_1 input').removeAttribute('checked')
    })
})(jQuery, undefined)
