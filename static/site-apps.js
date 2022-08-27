$(document).ready(function(){
    $('.slider').slick({
        dots: true,
        adaptiveHeight: true,
        pauseOnFocus: false,
        waitForAnimate: false
    });

    $('.product-list-item-content__img-slider').slick({
        dots: true,
        adaptiveHeight: true,
        pauseOnFocus: false,
        waitForAnimate: false
    }).hover(function(){
        $(this).slick('slickGoTo',1);
    }, function(){
        $(this).slick('slickGoTo',0, true);
    });

    $('.product__top-gallery--main-slider').slick({
        dots: true,
        arrows: false,
        adaptiveHeight: true,
        infinite: false,
        asNavFor:'.product__top-gallery--bottom-slider'
    });

    $('.product__top-gallery--bottom-slider').slick({
        adaptiveHeight: true,
        slidesToShow: 5,
        infinite: false,
        // centerMode: true,
        // centerPadding: '60px',
        asNavFor: '.product__top-gallery--main-slider',
        focusOnSelect: true
    });

    let t
    $('.top-catalog__first-level-item').hover(function(){
        $('.top-catalog__100w-bg').height($(this).children('.top-catalog__second-level-list-wrapper--w100').outerHeight());
        let innerWrapperToShow = $(this).children('div')
        t = setTimeout(function(){
            $('.darker-out-topmenu').addClass('darker-out-topmenu--active');
            $('.top-catalog__100w-bg').addClass('top-catalog__100w-bg--active');
            innerWrapperToShow.addClass('top-catalog__second-level-list-wrapper--w100--active');
        }, 400, innerWrapperToShow)
    }, function(){
        $('.darker-out-topmenu').removeClass('darker-out-topmenu--active');
        $('.top-catalog__100w-bg').removeClass('top-catalog__100w-bg--active');
        $(this).children('div').removeClass('top-catalog__second-level-list-wrapper--w100--active');
        clearTimeout(t);
    })

    let maxHeightSection = $('.category-sidebar').data('max-height-section');

    $('.category-sidebar__section-content').css('max-height', maxHeightSection)
    for (let i of $(".category-sidebar__section")) {
        let checkBox = $(i).children('div').children('div').children('label').children('input')
        let content = $(i).children(".category-sidebar__section-content-wrapper").children('.category-sidebar__section-content');
        if(checkBox.is(':checked')){
            // $('#'+checkBox.data('id')).css('display', 'block');
            $('#'+checkBox.val()).css('display', 'block');
        } else {
            // $('#'+checkBox.data('id')).css('display', 'none');
            $('#'+checkBox.val()).css('display', 'none');
        }

        if (content.prop('scrollHeight') - 23 > $(content).height()) {
            let wideBlock = $(content).next('div');
            let collapseBlock = $(wideBlock).next('div')

            wideBlock.css('display', 'block');

            $(i).css('margin-bottom', '0.5rem');
            wideBlock.on('click', function() {
                $(content).css('max-height', '100%');
                wideBlock.css('display', 'none');
                collapseBlock.css('display', 'block');
            })

            collapseBlock.on('click', function() {
                $(content).css('max-height', maxHeightSection);
                collapseBlock.css('display', 'none')
                wideBlock.css('display', 'block')
            })
        }
    }

    $('.category-sidebar__section :checkbox').change(function(){
        $('#'+$(this).val()).slideToggle('fast');
    })

    let slider = document.getElementById('slider');


    noUiSlider.create(slider, {
        start: [parseFloat($(slider).data('priceFrom')), parseFloat($(slider).data('priceTo'))],
        connect: true,
        step:1,
        range: {
            'min': parseFloat($(slider).data('minPrice')),
            'max': parseFloat($(slider).data('maxPrice'))
        },

    });
    var inputNumberFrom = document.getElementById('input-number-from');
    var inputNumberTo = document.getElementById('input-number-to');

    slider.noUiSlider.on('update', function (values, handle) {

        var value = values[handle];

        if (handle) {
            inputNumberTo.value = value;
        } else {
            inputNumberFrom.value = value;
        }
    });

    $('input[type=radio]').click(function(){
    // $('.category-sidebar__section-content input[type=checkbox]').click(function(){
        if ($('#slider').data('changed') == false) {
            $('#input-number-from').prop("disabled", true);
            $('#input-number-to').prop("disabled", true);
        }
        $('#filter-form').submit();
    })
    $('.category-sidebar__section-content input[type=checkbox]').click(function(){
        $('.category__paginator_item').first().prop( "checked", true );
        if ($('#slider').data('changed') == false) {
            $('#input-number-from').prop("disabled", true);
            $('#input-number-to').prop("disabled", true);
        }
        $('#filter-form').submit();
    })

    inputNumberFrom.addEventListener('change', function () {
        slider.noUiSlider.set([this.value, null]);
    });

    inputNumberTo.addEventListener('change', function () {
        slider.noUiSlider.set([null, this.value]);
    });

    $('.category-products__display-settings').click(function(){
        $(this).children('div').fadeIn('fast');
    })

    $(document).click(function(e){
        if (!$(e.target).closest('.category-products__display-settings').length) {
            $('.category-products__display-settings span').next().fadeOut();
        }
    })

    $('.category-products__filters-item').click(function(){
        let filter = $(this).data('filter');

        if (filter != 'price'){
            let val = $(this).data('val');
            $('input[name='+filter+'][value='+val+']').prop( "checked", false );
        }
        $('.category__paginator_item').first().prop( "checked", true );
        if ($('#slider').data('changed') == false | filter == 'price') {
            $('#input-number-from').prop("disabled", true);
            $('#input-number-to').prop("disabled", true);
        }
        $('#filter-form').submit();
    })
    $('#input-number-from, #input-number-to').change(function(){
        $('button').fadeIn('fast');
        $('#slider').data('changed', 'true')

    })
    slider.noUiSlider.on('change', function () {
        $('button').fadeIn('fast');
        $('#slider').data('changed', 'true')
    });


});