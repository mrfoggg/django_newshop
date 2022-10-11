$(document).ready(function(){
    let basketOpen = false;
    let autohideTimer;

    function hideFlowingViewed(){
        $('.viewed_products.flowing').removeClass('show');
        $('.viewed_products__flowing-ancor').removeClass('hidden');
        $('.viewed_products__darker').removeClass('viewed_products__darker--active')
    }

    function makeSubheaderFlowing(){
        if($(window).scrollTop() > $('.main-header').height()){
            $('.sub-header, .sub-header__search, .main-header__logo').addClass('slicky');
            $('.scroll-top').fadeIn();
        } else {
            $('.sub-header, .sub-header__search, .main-header__logo').removeClass('slicky');
            $('.scroll-top').fadeOut();
        }
    }

    function hideBasket(){
        $('#basket').slideUp(function (){
            basketOpen = false;
        });
        $('.sub-header__basket').removeClass('active');
        $('.hide_status').removeClass('active hidding');
    }

    function showBasket(doWhenOpen){
        $('#basket').slideDown(function () {
            basketOpen = true;
            doWhenOpen();
        });
        $('.sub-header__basket').addClass('active');
        $('.hide_status').addClass('active hidding');
    }

    function showBascketWithAutohide(doWhenOpen){
        showBasket(doWhenOpen);
        if (autohideTimer != undefined) {
            clearTimeout(autohideTimer);
        }
        autohideTimer = setTimeout(function(){
            hideBasket();
        }, 4000)

        $('#basket').hover(function(){
            $('.hide_status').removeClass('hidding active');
            clearTimeout(autohideTimer);
        }, function(){
            $('.hide_status').addClass('active hidding');
            clearTimeout(autohideTimer);
            autohideTimer = setTimeout(function(){
                hideBasket();
            }, 4000)
        });
    }

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

    function updateTotalBasket(total_amount, total_sum){
        $('.user-content__basket-total--ammount span, .sub-header__basket span').text(total_amount);
        $('.user-content__basket-total--summ span').text(total_sum);
        if (! total_amount){
            $('.sub-header__basket span, .user-content__basket-total').fadeOut();
            $('.user-content__basket-list').html($.parseHTML('<h2 id="empty_basket">Кошик порожній</h2>'))
        } else {
            $('.sub-header__basket span, .user-content__basket-total').fadeIn();
        }
    }

    makeSubheaderFlowing();

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
    });

    let maxHeightSection = $('.category-sidebar').data('max-height-section');

    $('.category-sidebar__section-content').css('max-height', maxHeightSection)
    for (let i of $(".category-sidebar__section")) {
        let checkBox = $(i).children('div').children('div').children('label').children('input')
        let content = $(i).children(".category-sidebar__section-content-wrapper").children('.category-sidebar__section-content');
        if(checkBox.is(':checked')){
            $('#'+checkBox.val()).css('display', 'block');
        } else {
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
    });

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

        let inputNumberFrom = document.getElementById('input-number-from');
        let inputNumberTo = document.getElementById('input-number-to');

        slider.noUiSlider.on('update', function (values, handle) {
            let value = values[handle];
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
        if ($('#slider').data('changed') == false) {
            $('#input-number-from').prop("disabled", true);
            $('#input-number-to').prop("disabled", true);
        }
        $('#filter-form').submit();
    });

    $('.category-sidebar__section-content input[type=checkbox]').click(function(){
        $('.category__paginator_item').first().prop( "checked", true );
        if ($('#slider').data('changed') == false) {
            $('#input-number-from').prop("disabled", true);
            $('#input-number-to').prop("disabled", true);
        }
        $('#filter-form').submit();
    });

    $('.category-products__display-settings').click(function(){
        $(this).children('div').fadeIn('fast');
    });

    $(document).click(function(e){
        if (!$(e.target).closest('.category-products__display-settings').length) {
            $('.category-products__display-settings span').next().fadeOut();
        }
        if (!$(e.target).closest('.viewed_products.flowing').length && ! $(e.target).is('span.viewed_products__flowing-ancor') ) {
            hideFlowingViewed();
        }
    });

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
    });

    $('#input-number-from, #input-number-to').change(function(){
        $('button').fadeIn('fast');
        $('#slider').data('changed', 'true')

    });

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
        })
    }

    $(document).on('select2:open', () => {
        document.querySelector('.select2-search__field').focus();
    });

    $(".django-select2[name='area']").on('select2:select', function(){
        $('.input-data-delivery-cost p:nth-child(3)').fadeIn().css('display', 'flex');
        $(".django-select2[name='settlement']").select2('open')
    });

    $(".django-select2[name='settlement']").on('select2:select', function(){
        $('.input-data-delivery-cost button').fadeIn().focus();
    });

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
    });

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

    function favoritesOrCompareActions (e){
        const target = $(e.target)
        const mode = target.data('mode');
        const form = target.nextAll('form');
        const page = form.data('page');
        let action;
        let statusWhenSuccess;
        const status = target.data('status');

        form.unbind('submit');
        form.submit(function (submitEvent){
            submitEvent.preventDefault();
            $('.preloader.fast').fadeIn('fast');

            if (status === 'disabled') {
                action = (mode === 'favorites') ? {'code':'add_fav', 'text_when_success': 'У обраному'} : {'code':'add_to_compare', 'text_when_success': 'У порівнянні'}
                statusWhenSuccess = 'enabled';
            }
            else {
                action = (mode === 'favorites') ? {'code':'remove_fav', 'text_when_success': 'До обраного'} : {'code':'remove_to_compare', 'text_when_success': 'До порівняння'}
                statusWhenSuccess = 'disabled';
            }

            target.nextAll('form').children('input[name="action"]').val(action.code)

            $.ajax({
                type: "POST",
                url: $(this).attr('action'),
                data: $(this).serialize(),
                success: function (response) {
                    target.data('status', statusWhenSuccess);
                    setTimeout(function (){
                        $('.preloader.fast').fadeOut('fast');
                        target.toggleClass('added', statusWhenSuccess === 'enabled');
                        if (page === 'product')
                            target.text(action.text_when_success);
                        if (page === 'favorites' && action.code === 'remove_fav')
                            target.parents('.product-list-item').fadeOut();
                        if (page === 'compare') {
                            const product_id = target.data('productId');
                            $(`td[data-product-id=${product_id}], th[data-product-id=${product_id}]`).fadeOut();
                        }
                        if (mode === 'favorites') {
                            $('.sub-header__favorites').html(`<span>${response['total_fav']}</span>`);
                            pulse($('.sub-header__favorites span'));
                            if (response['total_fav'] === 0)
                                $('.sub-header__favorites span').fadeOut();
                        } else {
                            $('.sub-header__compare').html(`<span>${response['total_comp']}</span>`);
                            pulse($('.sub-header__compare span'));
                            if (response['total_comp'] === 0)
                                $('.sub-header__compare span').fadeOut();
                        }
                    }, 400)
                }
            });
        });
        form.submit();
    }

    $(".product-list-item-content__icons span, .product__top-data-aсtions span, .compare th span").click(favoritesOrCompareActions);

    $(window).scroll(function(){
        hideFlowingViewed();
        hideBasket();
        makeSubheaderFlowing();
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
    }).init(function(){
        $('.top_products__content.slider-mode .product-list-item-content__img-slider-wrapper').css('display', 'flex')
    });

    $('.new_products__content.slider-mode').slick({
        slidesToShow: 5,
        slidesToScroll: 5,
        rows: 2,
        infinite: false,
        prevArrow: ".new_products .section-arrows--left",
        nextArrow: ".new_products .section-arrows--right",
    }).init(function(){
        $('.new_products__content.slider-mode .product-list-item-content__img-slider-wrapper').css('display', 'flex')
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
    }).init(function(){
        $('.viewed_slider_mode .product-list-item-content__img-slider-wrapper').css('display', 'flex')
    });

    $('.viewed_products__flowing-ancor').click(function(){
        $('.viewed_products__flowing-ancor').addClass('hidden');
        $('.viewed_products.flowing').addClass('show');
        $('.viewed_products__darker').addClass('viewed_products__darker--active');
    });

    $('.viewed_products .button-close').click(function(){
        hideFlowingViewed();
    });

    function changeBasket(e){
        const target = $(e.target)
        const product_id = target.data('product_id');
        const action = target.data('action');
        $('form#update_basket input[name="product_id"]').val(product_id);
        if (action === 'change_amount')
            $('form#update_basket input[name="amount"]').val(target.val());
        $('form#update_basket input[name="action"]').val(action);
        $('#basket').addClass('disabled');
        $('form#update_basket').unbind('submit');
        $('form#update_basket').submit({'this_input': $(e.target)}, function (e){
            e.preventDefault();
            $.ajax({
                type: "POST",
                url: $(this).attr('action'),
                data: $(this).serialize(),
                success: function (response) {
                    setTimeout(function (){
                        if (action === 'change_amount')
                            $(e.data.this_input).parent().next().children('span').text(response['sum']);
                        if (action === 'remove_from_basket'){
                            $(e.data.this_input).parents('.user-content__basket-item').fadeOut();
                            const productForm = $(`form.product_by_form[data-product_id="${product_id}"]`);
                            productForm.data('status', "not_in_basket");
                            productForm.children('button').text(productForm.data('by_text'));
                        }
                        updateTotalBasket(response['total_amount'], response['total_sum']);
                        $('#basket').removeClass('disabled');
                    }, 200)
                }
            });
        });
        $('form#update_basket').submit();
    }

    $('.user-content__basket-item-amount input').change(changeBasket);
    $('.user-content__basket-item span.close span').click(changeBasket);

    $(document).click(function(e){
        if (!$(e.target).closest('#basket').length && !$(e.target).closest('.sub-header__basket').length && basketOpen) {
            hideBasket();
        }
    });

    $('.sub-header__basket').click(function(){
        if (basketOpen)
            hideBasket();
        else
            showBascketWithAutohide(function (){});
    });


    $('.product_by_form').submit(function(e){
        e.preventDefault();
        $('.preloader.fast').fadeIn('fast');
        $.ajax({
            type: "POST",
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function (response) {
                setTimeout(function () {
                    $('.preloader.fast').fadeOut();
                    let htmlNewItem = $.parseHTML(`
                        <div class="user-content__basket-item" style="display: none">
                            <div class="user-content__basket-item-img">
<!--                                <img src="${response['thumb']}">-->
                                <a href="${response['pr_url']}"><img src="${response['thumb']}"></a>
                            </div>
                            <div class="user-content__basket-item-info">
<!--                                <h4>${response['name']}</h4>-->
                                <a href="${response['pr_url']}"><h4>${response['name']}</h4></a>
                                <div class="user-content__basket-item-calculate">
                                    <div class="user-content__basket-item-price"><span>${response['price']}</span></div>
                                    <div class="user-content__basket-item-amount">
                                        <input type="number" min="1" name="amount" value="1" data-product_id="${response['id']}" data-action="change_amount" autocomplete="off">, шт
                                    </div>
                                    <div class="user-content__basket-item-total">Всього: <span>${response['price']}</span> ₴</div>
                                </div>
                            </div>
                            <span class="close"><span data-product_id="${response['id']}" data-action="remove_from_basket"></span></span>
                        </div>`);

                    $(htmlNewItem).find('input').change(changeBasket);
                    $(htmlNewItem).find('span.close span').click(changeBasket);

                    let byedText = $(e.target).data('byed_text');
                    $(e.target).find('button').text(byedText);
                    $(e.target).data('status', 'in_basket');
                    $('.user-content__basket-list').append(htmlNewItem);
                    function doWhenOpen(){
                        $(htmlNewItem).delay(200).slideDown(500);
                    }
                    $('#empty_basket').remove();
                    $('.user-content__basket-total').addClass('visible');
                    updateTotalBasket(response['total_amount'], response['total_sum']);
                    if (! $('.sub-header__basket span').length){
                        $('.sub-header__basket').html('<span>1</span');
                    }
                    showBascketWithAutohide(doWhenOpen);
                }, 200)
            }
        });
    });



    $('.product_by_form button').click(function(e){
        let form = $(e.target).parent('form');
        if (form.data('status') == 'not_in_basket'){
            form.submit();
        } else {
            if(!basketOpen) {
                showBascketWithAutohide(function (){});
            }
        }
    });
});

document.body.onload = function() {
    setTimeout(function(){$('.preloader.slow').fadeOut(300)}, 100)
}