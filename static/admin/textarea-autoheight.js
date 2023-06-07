if (!$) {
    $ = django.jQuery;
}

$(document).ready(function (){
    const commentInputs = document.querySelectorAll('textarea');
    commentInputs.forEach(function (item){
        let itemH = item.offsetHeight;
        item.style.height = item.scrollHeight + 2 + 'px';
        item.addEventListener('input', function(e){
            e.target.style.height = itemH + 'px';
            e.target.style.height = e.target.scrollHeight + 2 + 'px';
        });
    });
});

