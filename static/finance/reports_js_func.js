$(document).ready(()=>{
    $.datetimepicker.setLocale('ru');
    $('#id_start, #id_end').datetimepicker({
        dayOfWeekStart: 1,
        maxDateTime: 0,
        format: "d.m.Y",
        timepicker:false
    });
    $('form').submit(function (e){
        console.log('SUBMIT');
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: window.location.href,
            data: $(this).serialize(),
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            success: function (response){
                $('#reportTable').text('');
                $('caption h3').text(response.caption)
                fill_table(response);
            }
        });
    })
});

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