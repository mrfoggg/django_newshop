$(document).ready((function(){let e;$(".slider").slick({dots:!0,adaptiveHeight:!0,pauseOnFocus:!1,waitForAnimate:!1}),$(".product-list-item-content__img-slider").slick({dots:!0,adaptiveHeight:!0,pauseOnFocus:!1,waitForAnimate:!1}).hover((function(){$(this).slick("slickGoTo",1)}),(function(){$(this).slick("slickGoTo",0,!0)})),$(".top-catalog__first-level-item").hover((function(){$(".top-catalog__100w-bg").height($(this).children(".top-catalog__second-level-list-wrapper--w100").outerHeight());let t=$(this).children("div");e=setTimeout((function(){$(".darker-out-topmenu").addClass("darker-out-topmenu--active"),$(".top-catalog__100w-bg").addClass("top-catalog__100w-bg--active"),t.addClass("top-catalog__second-level-list-wrapper--w100--active")}),400,t)}),(function(){$(".darker-out-topmenu").removeClass("darker-out-topmenu--active"),$(".top-catalog__100w-bg").removeClass("top-catalog__100w-bg--active"),$(this).children("div").removeClass("top-catalog__second-level-list-wrapper--w100--active"),clearTimeout(e)}));let t=$(".category-sidebar").data("max-height-section");$(".category-sidebar__section-content").css("max-height",t);for(let e of $(".category-sidebar__section")){let i=$(e).children("div").children("div").children("label").children("input"),o=$(e).children(".category-sidebar__section-content-wrapper").children(".category-sidebar__section-content");if(i.is(":checked")?$("#"+i.val()).css("display","block"):$("#"+i.val()).css("display","none"),o.prop("scrollHeight")-23>$(o).height()){let i=$(o).next("div"),c=$(i).next("div");i.css("display","block"),$(e).css("margin-bottom","0.5rem"),i.on("click",(function(){$(o).css("max-height","100%"),i.css("display","none"),c.css("display","block")})),c.on("click",(function(){$(o).css("max-height",t),c.css("display","none"),i.css("display","block")}))}}$(".category-sidebar__section :checkbox").change((function(){$("#"+$(this).val()).slideToggle("fast")}));var i=document.getElementById("slider");noUiSlider.create(i,{start:[0,19900],connect:!0,step:1,range:{min:0,max:19900}});var o=document.getElementById("input-number-from"),c=document.getElementById("input-number-to");i.noUiSlider.on("update",(function(e,t){var i=e[t];t?c.value=i:o.value=i})),$(".category-sidebar__section-content input").click((function(){$("#filter-form").submit()})),o.addEventListener("change",(function(){console.log(this.value),i.noUiSlider.set([this.value,null])})),c.addEventListener("change",(function(){i.noUiSlider.set([null,this.value])})),$(".category-products__display-settings").click((function(){$(this).children("div").slideToggle("fast")})),$(document).click((function(e){$(e.target).closest(".category-products__display-settings").length||$(".category-products__display-settings span").next().fadeOut()})),$(".category-products__filters-item").click((function(){let e=$(this).data("filter"),t=$(this).data("val");console.log(e),console.log(t),$("input[name="+e+"][value="+t+"]").prop("checked",!1),$("#filter-form").submit()}))}));