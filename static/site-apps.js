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


    function updateTotalBasket(total_amount, total_sum){
        $('.user-content__basket-total--ammount span, .sub-header__basket span').text(total_amount);
        $('.user-content__basket-total--summ span').text(total_sum);
        if (! total_amount){
            // прверить не на странице чекаута ли мы
            if ($('.checkout_header').length) {
                let url = $('.link_back')[0].href;
                console.log('url', url);
                window.history.replaceState({route: url}, "EVILEG", url);
                $('.link_back')[0].click();
            } else {
                $('.sub-header__basket span').fadeOut();
                $('.user-content__basket-total').removeClass('visible');
                $('.user-content__basket-list').html($.parseHTML('<h2 id="empty_basket">Кошик порожній</h2>'))
            }

        } else {
            // $('.sub-header__basket span, .user-content__basket-total').slideDown();
            $('.sub-header__basket span').fadeIn();
            $('.sub-header__basket span, .user-content__basket-total').addClass('visible');
        }
    }

    function initProductItem(){
        $('.product-list-item-content__img-slider').filter('.slick-initialized').slick('unslick');
        $('.slick-slide').remove();
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

        $('.product_by_form').submit(function(e){
            if (! $(this).data('byNow')){
                e.preventDefault();
                $('.preloader.fast').fadeIn('fast');
                $.ajax({
                    type: "POST",
                    url: $(this).attr('action'),
                    data: $(this).serialize(),
                    success: function (response) {
                        // console.log(response);
                        setTimeout(function () {
                            $('.preloader.fast').fadeOut();
                            function addElementsToBasket(element, pricesObj=false) {
                                let price = pricesObj ? pricesObj[element['id']] : element['price']
                                let htmlNewItem = $.parseHTML(`
                                    <div class="user-content__basket-item" style="display: none">
                                        <div class="user-content__basket-item-img">
                                            <a href="${element['pr_url']}"><img src="${element['thumb']}"></a>
                                        </div>
                                        <div class="user-content__basket-item-info">
                                            <a href="${element['pr_url']}"><h4>${element['name']}</h4></a>
                                            <div class="user-content__basket-item-calculate">
                                                <div class="user-content__basket-item-price"><span>${price}</span>&nbsp₴</div>
                                                <div class="user-content__basket-item-amount">
                                                    <input type="number" min="1" name="amount" value="1" data-product_id="${element['id']}" data-action="change_amount" autocomplete="off">, шт
                                                </div>
                                                <div class="user-content__basket-item-total">Всього: <span>${price}</span> ₴</div>
                                            </div>
                                        </div>
                                        <span class="close"><span data-product_id="${element['id']}" data-action="remove_from_basket"></span></span>
                                    </div>`);
                                $('.user-content__basket-list').append(htmlNewItem);

                                $(htmlNewItem).find('input').change(changeBasket);
                                $(htmlNewItem).find('span.close span').click(changeBasket);
                                function doWhenOpen(){
                                    $(htmlNewItem).delay(200).slideDown(500);
                                }
                                showBascketWithAutohide(doWhenOpen);
                            }

                            if ($('.product__main-data-sidebar__added_products li').length) {
                                for (let newElemData of response['added_products_data_list']) {
                                    addElementsToBasket(newElemData, response['prices_dict']);
                                }
                                if (! $('.sub-header__basket span').length){
                                    $('.sub-header__basket').html(`<span>${response["total_amount"]}</span>`);
                                }
                            } else {
                                addElementsToBasket(response);
                                if (! $('.sub-header__basket span').length){
                                    $('.sub-header__basket').html('<span>1</span');
                                }
                            }
                            let byedText = $(e.target).data('byed_text');
                            $(e.target).find('button[type="button"]').text(byedText);
                            $(e.target).data('status', 'in_basket');
                            $('#empty_basket').remove();
                            updateTotalBasket(response['total_amount'], response['total_sum'] + ' ₴');

                            $('.user-content__basket-total').addClass('visible');
                        }, 200)
                    }
                });
            }
        });

        $('.product_by_form button').click(function(e){

            let form = $(e.target).parent('form');

            if ($('.product__main-data-sidebar__added_products li').length) {
                $('.product_by_form input[name="action"]').val('multi_add_basket');
                let addictProductIdList = [$('.product_by_form input[name="product_id"]').val()];
                for (let li of $('.product__main-data-sidebar__added_products li')) {
                    addictProductIdList.push(($(li).data('value')).toString());
                }
                // console.log(addictProductIdList.join(','));
                $('.product_by_form input[name="product_id"]').val(addictProductIdList.join(','));
            } else {
                if ($('.product_by_form input[name="product_id"]').data('id')) {
                    $('.product_by_form input[name="product_id"]').val($('.product_by_form input[name="product_id"]').data('id'));
                    $('.product_by_form input[name="action"]').val('add_basket');
                }
            }

            if ($(e.target).data('byNow')){
                console.log($(form).data());
                console.log($(form).data('urlByNow'));
                $(form).attr('action', $(form).data('urlByNow'));
                $(form).data('byNow', true);
                console.log($(form).attr('action'));
            } else {
                if (form.data('status') === 'not_in_basket') {
                    form.submit();
                } else {
                    if(!basketOpen) {
                        showBascketWithAutohide(function (){});
                    }
                }
            }
        });

        // $(".product-list-item-content__icons span").click(favoritesOrCompareActions);
    }

    initProductItem();
    makeSubheaderFlowing();

    $('.slider').slick({
        dots: true,
        adaptiveHeight: true,
        pauseOnFocus: false,
        waitForAnimate: false
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

    function bindWideOreCollapseSectionContent(sectionContent){
        let wideBlock = $(sectionContent).next('div');
        let collapseBlock = $(wideBlock).next('div');
        $(wideBlock).on('click', function() {
            $(sectionContent).css('max-height', '100%');
            $(wideBlock).css('display', 'none');
            $(collapseBlock).css('display', 'block');
        })

        $(collapseBlock).on('click', function() {
            $(sectionContent).css('max-height', maxHeightSection);
            $(collapseBlock).css('display', 'none');
            $(wideBlock).css('display', 'block');
        })
    }

    $('.category-sidebar__section-content').css('max-height', maxHeightSection)
    for (let i of $(".category-sidebar__section")) {
        let checkBox = $(i).children('div').children('div').children('label').children('input')
        let content = $(i).children(".category-sidebar__section-content-wrapper").children('.category-sidebar__section-content');
        let wideBlock = $(content).next('div');
        // если чекбокс атоит контент секции показать
        if(! checkBox.is(':checked')){
            $('#'+checkBox.val()).css('display', 'block');
        } else {
            $('#'+checkBox.val()).css('display', 'none');
        }
        if ($(content).prop('scrollHeight') - 21 > $(content).height()) {
            $(wideBlock).css('display', 'block');
            $(content).css('margin-bottom', '0.5rem');
            bindWideOreCollapseSectionContent(content);
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

        slider.noUiSlider.on('set', function () {
            let values = this.get()
            $('#slider').data('priceFrom', values[0]);
            $('#slider').data('priceTo', values[1]);
            if (!$('#slider').data('reset'))
                filterFormSubmit(null, 'price');
        });
        slider.noUiSlider.on('start', function (){
             $('#slider').data('reset', false);
        });
        slider.noUiSlider.on('end', function (){
             console.log('END SET SLIDER');
        });


    }

    function filterFormSubmit(target, target_type){
        $('#filter-form').unbind('submit')
        $('#filter-form').submit({"target": target, 'target_type': target_type}, function (e){
            console.log('SUBMIT');

            e.preventDefault();
            let slider_data = $('#slider').data();
            let filterPriceNotChanged=Number(slider_data['minPrice']) === Number($('#input-number-from').val()) && Number(slider_data['maxPrice']) === Number($('#input-number-to').val());
            if (filterPriceNotChanged){
                $('.category-products__filters-item[data-filter="price"]').fadeOut(400,function (){
                    $(this).remove();
                })
            } else {
                // $('#input-number-from').prop("disabled", false);
                // $('#input-number-to').prop("disabled", false);

            }
            $('.category-products__list, .category-sidebar__checkbox, .category__header-info').css('opacity', '30%');
            if (filterPriceNotChanged) {
                $('#input-number-to, #input-number-from').prop('disabled', true);
            }
            if ($('#default_sort').prop('checked')) {
                $('#default_sort').prop('disabled', true);
            }
            if ($('#page_1').prop('checked')) {
                $('#page_1').prop('disabled', true);
            }
            let groupedFilterData = {};
            // получаем ссылку ЧПУ
            for (let inp of $('.category-sidebar__section-content input[type="checkbox"]:checked')) {
                $(inp).prop('disabled', true);
                $(inp).data('tempDisabled', true);
                if (groupedFilterData.hasOwnProperty(inp.name)) {
                    groupedFilterData[inp.name] += '--' + $(inp).val();
                } else {
                    groupedFilterData[inp.name] = $(inp).val();
                }
            }
            let readyHumanUrl = '';
            for (let filter in groupedFilterData) {
                if (readyHumanUrl === '') {
                    readyHumanUrl = filter;
                } else {
                    readyHumanUrl += ('__' + filter);
;                }
                readyHumanUrl += ('__' + groupedFilterData[filter]);
            }

            $.ajax({
                type: "POST",
                url: (readyHumanUrl) ? $(this).attr('action') + readyHumanUrl + '/' : $(this).attr('action'),
                data: $(this).serialize(),

                success: function (response){
                    $('#input-number-to, #input-number-from').prop('disabled', false);
                    $('#default_sort').prop('disabled', false);
                    $('#page_1').prop('disabled', false);
                    $('input[data-temp-disabled="true"]').prop('disabled', false);
                    if (! (e.data['target_type'] ==='paginator')) {
                        let newPaginatorItems = '';
                        for (let p of response['page_range']) {
                            newPaginatorItems += `<input class="category__paginator_item" form="filter-form" id="page_${p}" type="radio" name="paginator" value=${p} ${p===1 ? 'checked' : ''}> <label for="page_${p}">${p}</label>`
                        }
                        const newParsedPaginatorItems = $.parseHTML(newPaginatorItems);
                        $('.category-paginator__items-wrapper label, .category__paginator_item').remove();
                        $('.category-paginator__items-wrapper').append(newParsedPaginatorItems);
                        $('.category-paginator__items-wrapper input').change(function (){
                            filterFormSubmit(null, 'paginator');
                        });
                    }



                    // действия с блоком серий товаров
                    const productSeries = response['product_series'];
                    if (Object.keys(productSeries).length) {
                        let serIdList = Object.keys(productSeries);
                        let isRemovedOreAddedSomeSeries = false;

                        // очистка ненужных серий
                        if ($('.category-sidebar__section [data-filter-type="series"]').length){
                            for (let ch of $('input[name="series"]')){
                                if (! serIdList.includes($(ch).val())){
                                    $(ch).parent().fadeOut(function (){
                                        $(this).remove();
                                    })
                                    isRemovedOreAddedSomeSeries = true;
                                }
                            }
                        } else {
                            const blockSeriesParsedHtml = $.parseHTML(`
                                <div class="category-sidebar__section" style="display: none" data-filter-type="series">
                                    <div class="category-sidebar__title"> Серия товаров
                                        <label>
                                            <input type="checkbox" value='series' name="sections-status">
                                            <span></span>
                                        </label>
                                    </div>
                                    <div id='series' class="category-sidebar__section-content-wrapper">
                                        <ul class="category-sidebar__section-content" data-filter-type="series">
                                        </ul>
                                        <div class="category-sidebar__section-overflow-indicator">Показати всі</div>
                                        <div class="category-sidebar__section-overflow-indicator">Згорнути</div>
                                    </div>
                                </div>
                            `);
                            $('input[value="brands"]').parents('.category-sidebar__section').after($(blockSeriesParsedHtml));
                            $(blockSeriesParsedHtml).slideDown('slow');
                            bindWideOreCollapseSectionContent($(blockSeriesParsedHtml).find('.category-sidebar__section-content'));
                            $(blockSeriesParsedHtml).find('input').change(function (){
                                $('#series').slideToggle('fast');
                            })
                        }
                        // добавление новых серий
                        for (let serId of serIdList) {
                            const newVal = productSeries[serId];
                            if (!$(`input[name="series"][value=${serId}]`).length){
                                const newItemSeriesParsedHtml = $.parseHTML(`
                                    <li><label class="category-sidebar__checkbox">
                                        <input type="checkbox" name="series" value=${serId}>
                                        <div class="category-sidebar__checkbox--visible"></div> <span><span>${newVal['name']}</span> (<span class="category-sidebar__checkbox--total">${newVal['total_products']}</span>)</span>
                                    </label></li>
                                `);
                                $(newItemSeriesParsedHtml).find('input').click(function(e){
                                    $('.category__paginator_item').first().prop( "checked", true );
                                    filterFormSubmit(e.target, 'checkbox');
                                });
                                $('.category-sidebar__section-content[data-filter-type="series"]').append($(newItemSeriesParsedHtml));
                                isRemovedOreAddedSomeSeries = true
                            }
                        }
                        let seriesSectionContent =$('.category-sidebar__section[data-filter-type="series"]').find('.category-sidebar__section-content');
                        if (isRemovedOreAddedSomeSeries) {
                            setTimeout(function (){
                                if ($(seriesSectionContent).prop('scrollHeight') - 21 > $(seriesSectionContent).height()) {
                                    console.log('SHOW WIDER');
                                    $(seriesSectionContent).next('div').fadeIn();
                                } else if (!$(seriesSectionContent).next('div').next('div').height()) {
                                    console.log('HIDE WIDER');
                                    $(seriesSectionContent).next('div').fadeOut();
                                    bindWideOreCollapseSectionContent($(seriesSectionContent));
                                } else if ($(seriesSectionContent).height() < 260) {
                                    console.log('HIDE ALL');
                                    $(seriesSectionContent).next('div').next('div').fadeOut();
                                    $(seriesSectionContent).next('div').fadeOut();
                                } else if ($(seriesSectionContent).css('max-height') === '100%') {
                                    $(seriesSectionContent).next('div').next('div').fadeIn();
                                }
                            }, 900);
                        }
                    } else {
                        $('.category-sidebar__section[data-filter-type="series"]').fadeOut(function (){
                            $('.category-products__filters-item[data-filter="series"]').fadeOut();
                            $(this).remove();
                        });
                    }
                    $('html, body').animate({
                        scrollTop: $('.breadcrumbs').offset().top - 2*$('.breadcrumbs').height()
                    }, 600, 'linear');
                    let url;
                    if (this['data']) {
                        url = this['url'] + '?' + this['data'];
                    } else {
                        url = this['url'];
                    }
                    window.history.pushState({route: url}, "EVILEG", url);
                    if (response['checked_filters_len'] < 2){
                        $('#reset_all').fadeOut();
                    } else {
                        $('#reset_all').fadeIn();
                    }

                    if (e.data['target_type'] ==='checkbox'){
                        if ($(e.data['target']).is(':checked')){
                            const newCheckboxFilterDeleter = $.parseHTML(`<span class="category-products__filters-item" data-filter=${$(e.data.target).prop('name')} data-val=${$(e.data.target).val()}>${$(e.data.target).siblings('span').children('span:first-child').text()}</span>`);
                            bindFilterReseters($(newCheckboxFilterDeleter));
                            $(newCheckboxFilterDeleter).insertBefore('#reset_all');
                            if (response['checked_filters_len'] > 1)
                                $('#reset_all').css('visibility', 'visible');
                        } else {
                            $(`.category-products__filters-item[data-filter=${$(e.data['target']).prop('name')}][data-val=${$(e.data.target).val()}]`).fadeOut();
                        }

                    }

                    if (e.data['target_type']==='filters-item'){
                        $('#input-number-from, #input-number-to').prop('disabled', false);
                        $(e.data['target']).fadeOut(400, function (){
                            $(e.data['target']).remove();
                        });
                    }

                    if (e.data['target_type']==='price' && !filterPriceNotChanged){
                        if (!$('.category-products__filters-item[data-filter="price"]').length){
                            const newPriceFilterDeleter = $.parseHTML(`<span class="category-products__filters-item" data-filter="price">Ціна від &nbsp <span class="from">${$('#input-number-from').val()}</span> &nbsp грн до &nbsp <span class="to">${$('#input-number-to').val()}</span> &nbsp грн</span>`);
                            $(newPriceFilterDeleter).insertBefore('#reset_all');
                            bindFilterReseters($(newPriceFilterDeleter));
                        } else {
                            $('.category-products__filters-item .from').text($('#input-number-from').val());
                            $('.category-products__filters-item .to').text($('#input-number-to').val());
                        }
                    }

                    let listing = $.parseHTML(response['listing_html']);
                    // console.log(response['checked_filters']);
                    for (let filter of response['ajax_filters_data']) {
                        for (let val of filter['filter_values']){
                            let checkbox = $(`input[name=${filter['filter_slug']}][value=${val['value_slug']}]`)
                            checkbox.siblings('span').children('.category-sidebar__checkbox--total').text(val['total_products']);
                            if (val['total_products'] == 0 && checkbox.prop('checked') == false) {
                                checkbox.prop('disabled', true);
                                checkbox.parent().css('cursor', 'auto');
                            } else {
                                checkbox.prop('disabled', false);
                                checkbox.parent().css('cursor', 'pointer');
                            }
                        }
                    }

                    $('#category__header-info-total').text(response['total']);
                    $('#category__header-info-total-pages').text(response['total_pages']);
                    $('#category__header-info-current-page').text(response['current_page']);
                    $('.category-products__list').html(listing);
                    initProductItem();
                    $('.category-products__list .product-list-item').css('opacity', '0');
                    setTimeout(function (){
                        $('.category-products__list, .category-sidebar__checkbox, .category__header-info').css('opacity', '100%');
                        let duration = 100; //'slow'
                        $('.category-products__list .product-list-item').each(function(index) {
                            $(this).delay(duration * index).fadeTo('slow', 1);
                        });
                    },300)
                }
            });
        });
        $('#filter-form').submit();
    }


    $('input[type=radio]').change(function(){
        filterFormSubmit(null, null);
    });

    $('.category-sidebar__section-content input[type=checkbox]').click(function(e){
        $('.category__paginator_item').first().prop( "checked", true );

        filterFormSubmit(e.target, 'checkbox');
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

    $('input[name="listing_sort"]').change(function (e){
        $('.category-products__display-settings-popup').fadeOut();
        $('.category-products__display-settings span').text($(e.target).next().text());
    })

    function bindFilterReseters(target){
        // console.log('BIND RESET PRICE CLCK')
        target.click(function(e){
            let filter = $(this).data('filter');
            if (filter == 'price'){
                $('#slider').data('reset', false);
                // slider.noUiSlider.set([$('#slider').data('minPrice'), $('#slider').data('maxPrice')]);
                $('#slider').data('reset', true);
                setTimeout(function (){
                    slider.noUiSlider.set([$('#slider').data('minPrice'), $('#slider').data('maxPrice')]);
                },100)
                $('#slider').data('priceFrom', $('#slider').data('minPrice'));
                $('#slider').data('priceTo', $('#slider').data('maxPrice'));
                $('#input-number-from, #input-number-to').prop('disabled', true);
            } else {
                let val = $(this).data('val');
                $('input[name='+filter+'][value='+val+']').prop( "checked", false );
            }
            $('.category__paginator_item').first().prop( "checked", true );

            filterFormSubmit(this, 'filters-item');
            // $(e.target).fadeOut();
        });
    }

    //снятие фильтра вверху листинга

    bindFilterReseters($('.category-products__filters-item'));

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
            console.log('form.submit');
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
                    let targetId = target.siblings('form').children('input[name="product_id"]').val();
                    let targetType = target.data('mode');
                    let allSameTargets = $(`input[name="product_id"][value=${targetId}]`).parent('.product_action_form').siblings(`span[data-mode=${targetType}]`);
                    // менять статус и класс у всех товаров на странице с этим же id
                    allSameTargets.data('status', statusWhenSuccess);
                    setTimeout(function (){
                        $('.preloader.fast').fadeOut('fast');
                        allSameTargets.toggleClass('added', statusWhenSuccess === 'enabled');
                        // target.toggleClass('added', statusWhenSuccess === 'enabled');
                        if (page === 'product')
                            target.text(action.text_when_success);
                        if (page === 'favorites' && action.code === 'remove_fav'){
                            target.parents('.product-list-item').fadeOut(function (){
                                let thisCategoryList = $(this).parent()
                                $(this).remove();
                                if (! $(thisCategoryList).children().length) {
                                    $(thisCategoryList).parent().prev('h3').fadeOut();
                                    $(thisCategoryList).parent().slideUp(function () {
                                        $(this).remove();
                                        if (! $('.favorites__section').length) {
                                            $('.favorites-compare__title').after('<h3>Немає обраних товарів</h3>');
                                        }
                                    });
                                }
                            });
                        }

                        if (page === 'compare') {
                            const product_id = target.data('productId');
                            $(`td[data-product-id=${product_id}]`).fadeOut();
                            $(`th[data-product-id=${product_id}]`).fadeOut(function (){
                                let thisTable = $(this).parents('table');
                                $(this).remove();
                                if ($(thisTable).find('th').length < 2) {
                                    $(thisTable).slideUp("slow", function (){
                                        $(this).remove();
                                        if (! $('.compare table').length) {
                                            $('.favorites-compare__title').after('<h3>Немає товарів для порівняння</h3>')
                                        }
                                    });
                                }
                            });
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
                            productForm.children('button[type="button"]').text(productForm.data('by_text'));
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


    $('.product__main-data-sidebar-products-item input').change(function(){
        $(this).next('div').children('label').text('Додано');
        $(`input[name=${$(this).prop("name")}]`).not($(this)).next('div').children('label').text('Додати');
        let addedRow = $.parseHTML(`
            <li data-name=${$(this).prop('name')} data-value=${$(this).prop('value')} class='product__main-data-sidebar__added_products-item' style='display:none'>
                <span class="close"></span><span class='name'>${$(this).siblings('h5').text()}</span>, <span class='price'>${$(this).next('div').children('span').text()}</span>
            </li>
        `);
        $('#default_message').slideUp();
        $(addedRow).children('.close').click(function(){
            let idToDel = $(this).parent().data('value');
            let inpToUncheck = $(`input.addict_product[value=${idToDel}]`);
            $(inpToUncheck).prop('checked', false);
            $(inpToUncheck).next('div').children('label').text('Додати');
            $(this).parent().slideUp(function(){
                $(this).remove();
            });
            console.log($('.product__main-data-sidebar__added_products li').length);
            if ($('.product__main-data-sidebar__added_products li').length < 2) {
                $('#default_message').slideDown();
            }
        });
        $(`.product__main-data-sidebar__added_products-item[data-name='${$(this).prop("name")}']`).remove();

        $('.product__main-data-sidebar__added_products').append(addedRow);
        $(addedRow).slideDown();
        $('.product__main-data-sidebar h3').text('Обрані супутні товари');
    });

    if($('.checkout_header').length && !$('.user-content__basket-item').length){
        $('.link_back')[0].click();
    }

    if($('.content-wrapper.compare').length){
        $('.sub-header__compare').css('cursor', 'auto');
        $('.sub-header__compare').click(function (e){
            e.preventDefault();
        })
    }

    if($('.content-wrapper.favorites').length){
        $('.sub-header__favorites').css('cursor', 'auto');
        $('.sub-header__favorites').click(function (e){
            e.preventDefault();
        })
    }


});

document.body.onload = function() {
    setTimeout(function(){$('.preloader.slow').fadeOut(300)}, 100)
}