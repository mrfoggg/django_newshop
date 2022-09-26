$(document).ready(function(){
    function hideFlowingViewed(){
        $('.viewed_products.flowing').removeClass('show');
        $('.viewed_products__flowing-ancor').removeClass('hidden');
        $('.viewed_products__darker').removeClass('viewed_products__darker--active')
    }
    $('.slider').slick({
        dots: true,
        adaptiveHeight: true,
        pauseOnFocus: false,
        waitForAnimate: false
    });

    $('.product-list-item-content__img-slider').slick({
        dots: true,
        // adaptiveHeight: true,
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
        // adaptiveHeight: true,
        infinite: true,
        asNavFor:'.product__top-gallery--bottom-slider'
    });

    $('.product__top-gallery--bottom-slider').slick({
        adaptiveHeight: true,
        slidesToShow: 5,
        infinite: true,
        centerMode: true,
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

    if (document.getElementById('slider')) {


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

        inputNumberFrom.addEventListener('change', function () {
            slider.noUiSlider.set([this.value, null]);
        });

        inputNumberTo.addEventListener('change', function () {
            slider.noUiSlider.set([null, this.value]);
        });

        slider.noUiSlider.on('change', function () {
            $('button').fadeIn('fast');
            $('#slider').data('changed', 'true')
        });
    }

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

    $('.category-products__display-settings').click(function(){
        $(this).children('div').fadeIn('fast');
    })

    $(document).click(function(e){
        if (!$(e.target).closest('.category-products__display-settings').length) {
            $('.category-products__display-settings span').next().fadeOut();
        }
        if (!$(e.target).closest('.viewed_products.flowing').length && ! $(e.target).is('span.viewed_products__flowing-ancor') ) {
            hideFlowingViewed();
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
    // $('.phone-number-input').prop('maxlength', '9');

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
    $('.phone-number-input').click(function(){
        if (!$(this).is(":focus")) {
            $(this).setCursorPosition(0);
        }
      }).prop('maxlength', '9').mask("99)  999-99-99", {
        completed: function(){
            $("#ok_button").prop("disabled", false)
        }
      });

    $('.product__top-gallery-img-wrapper img').imagezoomsl({
        cursorshade: true,
        // disablewheel: false
        cursorshadeborder: '1px solid #A93CF3',
    });

    $('.product__tabs-item a, .scroll-top').mPageScroll2id({
        // layout:"horizontal"
        clickedClass: 'product__tabs-item--active',
        highlightClass: 'product__tabs-item--active',
        keepHighlightUntilNext: true,
        forceSingleHighlight: true,
        scrollSpeed: 500
    });
    if ($(".django-select2").length){
        $(".django-select2").djangoSelect2({
            language: "uk",
            theme: "flat"
            // theme: "classic"
        })
    }

    $(document).on('select2:open', () => {
        document.querySelector('.select2-search__field').focus();
    })

    $(".django-select2[name='area']").on('select2:select', function(){
        $('.input-data-delivery-cost p:nth-child(3)').fadeIn().css('display', 'flex');
        $(".django-select2[name='settlement']").select2('open')
    })

    $(".django-select2[name='settlement']").on('select2:select', function(){
        $('.input-data-delivery-cost button').fadeIn().focus();
    })

    $('#get_delivery_cost').submit(function (e){
        e.preventDefault();
        $('.input-data-delivery-cost-preloader').fadeIn();
        $.ajax({
            type: "POST",
            url: $(this).data('url'),
            data: $(this).serialize(),
            success: function (response){
                const cost_redelivery = parseInt(response['cost_redelivery']);
                const CostWarehouseWarehouse = parseInt(response['CostWarehouseWarehouse']);
                const CostWarehouseDoors = parseInt(response['CostWarehouseDoors']);
                const ProductCost = parseInt(response['Cost']);
                $('#settlement_to').text('До населеного пункту ' + response['settlement_to_name']);
                $('#cost_redelivery').text(cost_redelivery);
                $('#CostWarehouseWarehouse').text(CostWarehouseWarehouse);
                $('#CostWarehouseWarehouseMoney').text(CostWarehouseWarehouse + cost_redelivery);
                $('#CostWarehouseDoors').text(CostWarehouseDoors);
                $('#CostWarehouseDoorsMoney').text(CostWarehouseDoors + cost_redelivery);
                $('#CostWarehouseWarehouseProductCost').text(CostWarehouseWarehouse + ProductCost);
                $('#CostWarehouseWarehouseMoneyProductCost').text(CostWarehouseWarehouse + cost_redelivery + ProductCost);
                $('#CostWarehouseDoorsProductCost').text(CostWarehouseDoors + ProductCost);
                $('#CostWarehouseDoorsMoneyProductCost').text(CostWarehouseDoors + cost_redelivery + ProductCost);
                $('#Cost').text(ProductCost);
                $('.open-delivery-cost-popup').trigger( "click" );
                $('.input-data-delivery-cost-preloader').fadeOut();
            },
            error: function (response){
                $('.open-delivery-cost-popup-error').trigger( "click" );
                $('.input-data-delivery-cost-preloader').fadeOut();
            }
        })
    })
    $('.open-delivery-cost-popup').magnificPopup({
        type:'inline',
        midClick: true // Allow opening popup on middle mouse click. Always set it to true if you don't provide alternative source in href.
    });
    $('.open-delivery-cost-popup-error').magnificPopup({
        type:'inline',
        midClick: true // Allow opening popup on middle mouse click. Always set it to true if you don't provide alternative source in href.
    });

    $('.product__main-data-sidebar-products-slider').slick({
        dots: true,
    });

    $('.product_action_form').submit(function (e){
        console.log('SUBMIT');
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function (response){
            }
        })
    })

    function pulse(indicator){
        indicator.addClass('animated');
        setTimeout(function (element){
            element.removeClass('animated');
        },2000, indicator)
    }
    function increaseLovedCount(){
        let loved_count = $('.sub-header__favorites span').text();
        if (loved_count.length){
                $('.sub-header__favorites span').text(Number(loved_count) + 1);
            } else {
                $('.sub-header__favorites').html('<span>1</span>');
            }
        pulse($('.sub-header__favorites span'));
    }

    function decreaseLovedCount(){
        let loved_count = $('.sub-header__favorites span').text();
        if (loved_count > 1){
                $('.sub-header__favorites span').text(Number(loved_count) - 1);
            } else {
                $('.sub-header__favorites span').remove('span');
            }
        pulse($('.sub-header__favorites span'));
    }

    function increaseCompareCount(){
        let compare_count = $('.sub-header__compare span').text();
            if (compare_count.length){
                $('.sub-header__compare span').text(Number(compare_count) + 1);
            } else {
                $('.sub-header__compare').html('<span>1</span>');
            };
        pulse($('.sub-header__compare span'));
    }

    function decreaseCompareCount(){
        let compare_count = $('.sub-header__compare span').text();
            if (compare_count > 1){
                $('.sub-header__compare span').text(Number(compare_count) - 1);
            } else {
                $('.sub-header__compare span').remove('span');
            }
        pulse($('.sub-header__compare span'));
    }


    $(".product-list-item-content__add-favorite, .product__top-data-favorites").click(function (e){
        const form = $(e.target).nextAll('form');
        const action_field = form.children('input[name="action"]')
        if ($(e.target).data('status') == 'disabled'){
            $(e.target).data('status', 'enabled').addClass('loved')
            action_field.val('add_fav');

            if (form.data('mode') == 'product_view'){
                $(e.target).text('У обраному');
            }
            increaseLovedCount();
        } else {
            $(e.target).data('status', 'disabled').removeClass('loved');
            action_field.val('remove_fav');
            if (form.data('mode') == 'product_view'){
                $(e.target).text('До обраного');
            }
            decreaseLovedCount();
        }
        form.submit();
        if (form.data('mode') == 'favorites') {
            $(e.target).parents('.product-list-item').fadeOut();
        }
    })

    $(".product-list-item-content__compare, .product__top-data-compare").click(function (e){
        const form = $(e.target).nextAll('form');
        const action_field = form.children('input[name="action"]');
        if ($(e.target).data('status') == 'disabled'){
            $(e.target).data('status', 'enabled').addClass('compared');
            action_field.val('add_to_compare');
            if (form.data('mode') == 'product_view'){
                $(e.target).text('У порівнянні');
            }
            increaseCompareCount();
        } else {
            $(e.target).data('status', 'disabled').removeClass('compared');
            action_field.val('remove_to_compare');

            if (form.data('mode') == 'product_view'){
                $(e.target).text('До порівняння');
            }
            decreaseCompareCount()
        }
        form.submit();
    });

    $(".compare th span").click(function (e){
        const form = $(e.target).nextAll('form');
        form.submit();
        const product_id = $(e.target).parent('th').data('productId');
        $(`td[data-product-id=${product_id}], th[data-product-id=${product_id}]`).fadeOut();
        decreaseCompareCount();
    });

    $(window).scroll(function(){
        hideFlowingViewed();
        if($(window).scrollTop() > $('.main-header').height()){
            $('.sub-header, .sub-header__search, .main-header__logo').addClass('slicky');
            $('.scroll-top').fadeIn();
        } else {
            $('.sub-header, .sub-header__search, .main-header__logo').removeClass('slicky');
            $('.scroll-top').fadeOut();
        }
        let scrollBottom = $(document).height() - $(window).height() - $(window).scrollTop();
        const viewedBottom = $('footer').outerHeight() + $('.viewed_products').outerHeight();
        if (scrollBottom > viewedBottom) {
            $('.viewed_products__flowing-ancor').fadeIn();
        } else {
            $('.viewed_products__flowing-ancor').fadeOut();
        }
    });

    $('.top-categories__content').slick({
        adaptiveHeight: true,
        slidesToShow: 5,
        infinite: false,
        prevArrow: ".top-categories .arrow--left",
        nextArrow: ".top-categories .arrow--right",
    });

    $('.top_products__content.slider-mode').slick({
        slidesToShow: 5,
        slidesToScroll: 5,
        rows: 2,
        infinite: false,
        prevArrow: ".top_products .section-arrows--left",
        nextArrow: ".top_products .section-arrows--right",
    });
    $('.new_products__content.slider-mode').slick({
        slidesToShow: 5,
        slidesToScroll: 5,
        rows: 2,
        infinite: false,
        prevArrow: ".new_products .section-arrows--left",
        nextArrow: ".new_products .section-arrows--right",
    });

    $('.static .viewed_products__content.viewed_slider_mode').slick({
        slidesToShow: 5,
        slidesToScroll: 5,
        infinite: false,
        prevArrow: ".static.viewed_products .arrow--left",
        nextArrow: ".static.viewed_products .arrow--right",
    });

    $('.flowing .viewed_products__content.viewed_slider_mode').slick({
        slidesToShow: 5,
        slidesToScroll: 5,
        infinite: false,
        prevArrow: ".flowing.viewed_products .arrow--left",
        nextArrow: ".flowing.viewed_products .arrow--right",
    });


    $('.viewed_products__flowing-ancor').click(function(){
        $('.viewed_products__flowing-ancor').addClass('hidden');
        $('.viewed_products.flowing').addClass('show');
        $('.viewed_products__darker').addClass('viewed_products__darker--active');
    });

    $('.viewed_products .button-close').click(function(){
        hideFlowingViewed();
    });
});