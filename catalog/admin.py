import copy

import nested_admin
from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin, SortableTabularInline
from baton.admin import MultipleChoiceListFilter
from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
# from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.encoding import force_str
# from django.utils.translation import gettext as _
# from django.utils.translation import gettext_lazy
from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin

from finance.admin import ProductPriceProductInline
from ROOTAPP.models import Person

from .admin_forms import (AttributeForm, CategoryForm,
                          CombinationOfCategoryAdminForm, GroupForm,
                          GroupPlacementInlineFS,
                          GroupPositionInCombinationOfCategoryInLineFS,
                          MainAttrPositionInCombinationOfCategoryInLineFS,
                          ProductForm, ProductPlacementInlineForProductFS,
                          ShotAttrPositionInCombinationOfCategoryInLineFS)
from .models import (Attribute, Brand, Category, CategoryAddictProduct,
                     CombinationOfCategory, Country, Discount, Filter,
                     FixedTextValue, Group, GroupPlacement,
                     GroupPositionInCombinationOfCategory, MainAttribute,
                     MainAttrPositionInCombinationOfCategory, OtherShop,
                     PricesOtherShop, Product, ProductImage, ProductPlacement,
                     ProductSeries, ShotAttribute,
                     ShotAttrPositionInCombinationOfCategory, UnitOfMeasure, ProductSupplierPrice)
from .services import (DeleteQSMixin, clean_combination_of_category,
                       create_group_placement_at_end_combination,
                       create_main_attr_placement_at_end_combination,
                       create_shot_attr_placement_at_end_combination,
                       get_changes_in_categories_fs, get_changes_in_groups_fs,
                       remove_keys_in_products,
                       remove_keys_in_products_in_qs_deleted_attr,
                       set_prod_pos_to_end, update_combination_in_fs_product)


@admin.action(description='Сериализовать')
def export_as_json(modeladmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    serializers.serialize("json", queryset, stream=response)
    return response


class CategoryAddictProductInlineAdmin(nested_admin.NestedTabularInline):
    model = CategoryAddictProduct
    # ordering = ('position',)
    sortable_field_name = 'position'
    extra = 0


class ProductPlacementInlineForCategory(SortableTabularInline):
    readonly_fields = ('product', 'category_placement')
    model = ProductPlacement
    extra = 0
    fields = ('product', 'category_placement', 'product_position')
    sortable_field_name = 'product_position'
    ordering = ('product_position',)
    can_delete = False

    @admin.display(description='Содержится в категориях')
    def category_placement(self, obj):
        return obj.product.category_placement


class ProductPlacementInlineForProduct(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    formset = ProductPlacementInlineForProductFS
    readonly_fields = ('groups_list',)
    model = ProductPlacement
    extra = 0
    fields = ('category', 'groups_list', 'category_position')
    sortable_field_name = 'category_position'
    ordering = ('category_position',)

    @admin.display(description="Содержит группы атрибутов")
    def groups_list(self, obj):
        return obj.category.groups_list


class GroupPlacementInline(SortableInlineAdminMixin, admin.TabularInline):
    formset = GroupPlacementInlineFS
    readonly_fields = ('attributes_list',)
    model = GroupPlacement
    extra = 0
    fields = ('group', 'attributes_list', 'position')
    ordering = ['position']

    @admin.display(description='Содержжит атрибуты')
    def attributes_list(self, obj):
        return obj.group.attributes_list


class AttributeInline(SortableTabularInline):
    # class AttributeInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = Attribute
    # readonly_fields = ('name', 'type_of_value', 'unit_of_measure', 'fixed_values_list',)
    readonly_fields = ('fixed_values_list',)
    fields = ('name', 'slug', 'type_of_value', 'unit_of_measure', 'fixed_values_list', 'default_str_value', 'position')
    prepopulated_fields = {"slug": ("name",)}
    show_change_link = True
    extra = 0


class FixedTextValueInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = FixedTextValue
    prepopulated_fields = {"slug": ("name",)}
    extra = 0


class FilterInline(SortableTabularInline):
    model = Filter
    extra = 0
    ordering = ['position']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = Attribute.objects.filter(group_id__in=request._self_groups_).exclude(type_of_value=1)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# class BroCategoriesFilterInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
#     model = BroCategoriesFilter
#     extra = 0
#     fk_name = 'bro_category'
#
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == 'attribute':
#             kwargs["queryset"] = Attribute.objects.filter(group_id__in=request._self_groups_).exclude(type_of_value=1)
#         return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GroupPositionInCombinationOfCategoryInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    extra = 0
    readonly_fields = ('group_placement',)
    formset = GroupPositionInCombinationOfCategoryInLineFS
    model = GroupPositionInCombinationOfCategory
    # can_delete = False


class MainAttributeInLine(SortableTabularInline):
    model = MainAttribute
    ordering = ['position']
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = Attribute.objects.filter(group_id__in=request._self_groups_)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ShotAttributeInLine(SortableTabularInline):
    model = ShotAttribute
    extra = 0
    ordering = ['position']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = Attribute.objects.filter(group_id__in=request._self_groups_)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MainAttrPositionInCombinationOfCategoryInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = MainAttrPositionInCombinationOfCategory
    extra = 0
    readonly_fields = ('main_attribute',)
    formset = MainAttrPositionInCombinationOfCategoryInLineFS


class ShotAttrPositionInCombinationOfCategoryInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = ShotAttrPositionInCombinationOfCategory
    extra = 0
    readonly_fields = ('shot_attribute',)
    formset = ShotAttrPositionInCombinationOfCategoryInLineFS


class PricesOtherShopInline(nested_admin.NestedTabularInline):
    model = PricesOtherShop


class ProductImageInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    fields = ['position', ('image', 'name',)]
    model = ProductImage
    sortable_field_name = "position"
    extra = 0


class DiscountInline(nested_admin.NestedTabularInline):
    model = Discount
    extra = 0


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin, SummernoteModelAdmin, SortableAdminBase, admin.ModelAdmin, ):
    form = CategoryForm
    save_on_top = True
    list_display = ('tree_actions', 'indented_title', 'groups_list',)
    prepopulated_fields = {"slug": ("name",)}
    summernote_fields = ('description',)
    save_as = True
    save_as_continue = False
    inlines = (GroupPlacementInline, MainAttributeInLine, ShotAttributeInLine, ProductPlacementInlineForCategory,
               FilterInline,)
    actions = [export_as_json]

    class Media:
        ordering = ['name']
        default_order_field = 'name'
        default_order_direction = ''

        css = {
            "all": ("category_admin.css",)
        }

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            request._self_groups_ = GroupPlacement.objects.filter(category_id=obj.id).values_list('group_id', flat=True)
        else:
            request._self_groups_ = []
        return super(CategoryAdmin, self).get_form(request, obj, **kwargs)

    def delete_selected_tree(self, modeladmin, request, queryset):
        if request.POST.get("post"):
            n = 0
            with queryset.model._tree_manager.delay_mptt_updates():
                updated_products_list = []
                for obj in queryset:
                    if self.has_delete_permission(request, obj):
                        obj_display = force_str(obj)
                        self.log_deletion(request, obj, obj_display)
                        products_to_update = self.delete_model(request, obj, once_del=False)
                        if products_to_update:
                            updated_products_list.extend(products_to_update)
                        n += 1
            count_prod = Product.objects.bulk_update(updated_products_list, ['characteristics'])
            self.message_user(
                request, f"Успешно удалено {n} категорий, обновлен набор характеристик для {count_prod} товаров"
            )

            # Return None to display the change list page again
            return None
        else:
            # (ab)using the built-in action to display the confirmation page
            return delete_selected(self, request, queryset)

    def delete_model(self, request, obj, once_del=True):
        products_to_update = None
        clean_combination_of_category(obj)
        if obj.productplacement_set.exists() and Attribute.objects.filter(group__categories=obj):
            products = list(Product.objects.filter(categories=obj))
            keys_to_del = Attribute.objects.filter(group__categories=obj).values_list('slug', flat=True)
            products_to_update = remove_keys_in_products(keys_to_del, products)
            if once_del:
                count_prod = Product.objects.bulk_update(products_to_update, ['characteristics'])
                self.message_user(
                    request, f"Удалены некоторые характеристики для {count_prod} товаров"
                )
        obj.delete()
        return products_to_update

    def save_related(self, request, form, formsets, change):

        groups_fs = formsets[0]
        groups_fs.save()
        deleted_groups_list, sorted_added_group_placement_id_list = get_changes_in_groups_fs(groups_fs)

        main_attr_fs = formsets[1]
        main_attr_fs.save()
        added_main_attr_placement_id_list = [fs.id for fs in sorted(main_attr_fs.new_objects, key=lambda x: x.position)]

        shot_attr_fs = formsets[2]
        shot_attr_fs.save()
        added_shot_attr_placement_id_list = [fs.id for fs in sorted(shot_attr_fs.new_objects, key=lambda x: x.position)]

        formsets[3].save()
        formsets[4].save()

        combinations = CombinationOfCategory.objects.filter(categories=(category := groups_fs.instance))
        if sorted_added_group_placement_id_list:
            combinations = combinations.annotate(max_group_position=Max('group_position__position'))
        if added_main_attr_placement_id_list:
            combinations = combinations.annotate(max_main_attr_position=Max('main_attr_positions__position'))
        if added_shot_attr_placement_id_list:
            combinations = combinations.annotate(max_shot_attr_position=Max('shot_attr_positions__position'))

        if sorted_added_group_placement_id_list:
            create_group_placement_at_end_combination(combinations, sorted_added_group_placement_id_list)

        if added_main_attr_placement_id_list:
            create_main_attr_placement_at_end_combination(combinations, added_main_attr_placement_id_list)

        if added_shot_attr_placement_id_list:
            create_shot_attr_placement_at_end_combination(combinations, added_shot_attr_placement_id_list)

        if deleted_groups_list:
            # products_to_update = remove_characteristics_keys(category=groups_fs.instance, group=deleted_groups_list)
            products = Product.objects.filter(categories=groups_fs.instance)
            keys_to_del = Attribute.objects.filter(group__in=deleted_groups_list).values_list('slug', flat=True)
            Product.objects.bulk_update(remove_keys_in_products(keys_to_del, products), ['characteristics'])
            MainAttribute.objects.filter(attribute__group_id__in=deleted_groups_list).delete()
            ShotAttribute.objects.filter(attribute__group_id__in=deleted_groups_list).delete()


class BrandListFilter(MultipleChoiceListFilter):
    title = 'Бренд'
    parameter_name = 'brand__in'

    def lookups(self, request, model_admin):
        return Brand.objects.values_list('id', 'name')


@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin, SummernoteModelAdmin):
    form = ProductForm
    # fields = ['name', 'slug', 'admin_category', 'characteristics', 'combination_of_categories']
    list_display = ('name', 'category_placement')
    prepopulated_fields = {"slug": ("name",)}
    save_on_top = True
    inlines = (ProductPlacementInlineForProduct, PricesOtherShopInline, ProductImageInline, ProductPriceProductInline,
               CategoryAddictProductInlineAdmin, DiscountInline)
    # formfield_overrides = {
    #     models.JSONField: {'widget': JSONEditorWidget},
    # }
    search_fields = ('name', 'sku', 'admin_category__name')
    ordering = ('name',)
    readonly_fields = ('get_sorted_groups', 'combination_of_categories', 'full_current_price_info',
                       'supplier_prices_str', 'rate')
    summernote_fields = ('description',)
    change_form_template = "product_changeform.html"
    actions = [export_as_json]
    list_filter = ('admin_category', BrandListFilter)
    view_on_site = True
    fieldsets = (
        ("Основное", {
            'fields': (
                ('name', 'sku', 'sku_manufacturer', 'rating', 'is_active'),
                ('full_current_price_info', 'rate',), ('supplier_prices_str', 'main_supplier'),
                ('slug', 'admin_category'),
                ('brand', 'country_of_manufacture',),
                ('series', 'url'),
            ),
            'classes': ('tab-fs-none',),
        }),

        ("Габбариты и вес",
         {'fields': (
             ('length', 'width', 'height',), ('package_length', 'package_width', 'package_height'),
             ('weight', 'seats_amount')),
             'classes': ('tab-fs-none',),
         }),

        ("Характеристики", {
            # 'classes': ('collapse',),
            'fields': (
                ('characteristics',),
                ('description',),
            ),
            'classes': (
                'order-0', 'baton-tabs-init', 'baton-tab-inline-productplacement', 'baton-tab-inline-pricesothershop',

            ),
        })

    )

    class Media:
        css = {
            "all": ("admin/admin-changeform.css",)
        }

    def save_related(self, request, form, formsets, change):
        # сохраняем FormSet иначе 'ProductPlacementFormFormSet' object has no attribute 'deleted_objects'
        category_fs = formsets[0]
        category_fs.save()
        deleted_categories_list, added_categories_id_list = get_changes_in_categories_fs(category_fs)

        formsets[1].save()
        formsets[2].save()
        formsets[3].save()
        formsets[4].save()
        formsets[5].save()
        # formsets[6].save()

        if added_categories_id_list:
            set_prod_pos_to_end(category_fs, added_categories_id_list)

        if deleted_categories_list:
            # remove_characteristics_keys(product=category_fs.instance, category=deleted_categories_list)
            keys_to_del = Attribute.objects.filter(
                group__categories__in=deleted_categories_list).values_list('slug', flat=True)
            remove_keys_in_products(keys_to_del, [category_fs.instance])

        # проверить работу
        if deleted_categories_list or added_categories_id_list:
            update_combination_in_fs_product(category_fs)

        category_fs.instance.save()

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + ('characteristics',) if obj is None else self.readonly_fields

    def response_change(self, request, obj):
        if "_save_copy" in request.POST:
            obj.save()
            product_copy = copy.copy(obj)
            product_copy.id, product_copy.slug, product_copy.sku, product_copy.sku_manufacturer = None, None, None, None
            product_copy.url = None
            product_copy.name = obj.name + ' - копия'
            if Product.objects.filter(name=product_copy.name).exists():
                raise ValidationError("Копия с таким названием уже существует")
            product_copy.save()
            related_categories_product_pos = {x[0]: (0 if x[1] is None else x[1])
                                              for x in Category.objects.annotate(last_product_position=Max(
                    'productplacement__product_position')).filter(
                    productplacement__product=obj).values_list('id', 'last_product_position')}
            placements_to_create = [
                ProductPlacement(
                    product=product_copy, category_id=cat, product_position=related_categories_product_pos[cat] + 1)
                for cat, pos in related_categories_product_pos.items()]
            ProductPlacement.objects.bulk_create(placements_to_create)
            ProductImage.objects.bulk_create([
                ProductImage(product=product_copy, image=pr_pl[0], position=pr_pl[1])
                for pr_pl in ProductImage.objects.filter(product=obj).values_list('image', 'position')
            ])
            return HttpResponseRedirect(reverse('admin:catalog_product_change', args=(product_copy.id,)))
        return super().response_change(request, obj)

    def view_on_site(self, obj):
        return reverse('main_page:category_and_product', args=(obj.slug,))


@admin.register(Group)
# class GroupAdmin(DeleteQSMixin, nested_admin.NestedModelAdmin, ):
class GroupAdmin(DeleteQSMixin, SortableAdminBase, admin.ModelAdmin):
    form = GroupForm
    list_display = ('name', 'attributes_list')
    inlines = (AttributeInline,)
    search_fields = ('name',)

    class Media:
        css = {
            "all": ("hide_inline_action_admin.css",)
        }

    def delete_queryset(self, request, queryset):
        # print(f'{queryset=}')
        updated_product_dict = {}
        first_iter = True
        for obj in queryset:
            keys_to_del = Attribute.objects.filter(group=obj).values_list('slug', flat=True)
            products_to_update = list(Product.objects.filter(categories__groups=obj))
            remove_keys_in_products_in_qs_deleted_attr(
                keys_to_del, products_to_update, updated_product_dict, first_iter)
            first_iter = False
        Product.objects.bulk_update(updated_product_dict.values(), ['characteristics'])
        queryset.delete()

    def delete_model(self, request, obj):
        if obj.attributes.exists() and Product.objects.filter(categories__groups=obj).exists():
            keys_to_del = Attribute.objects.filter(group=obj).values_list('slug', flat=True)
            products_to_update = list(Product.objects.filter(categories__groups=obj))
            updated_products = remove_keys_in_products(keys_to_del, products_to_update)
            count_prod = Product.objects.bulk_update(updated_products, ['characteristics'])
            self.message_user(
                request, f"Удалены некоторые характеристики для {count_prod} товаров"
            )
        obj.delete()


@admin.register(Attribute)
class AttributeAdmin(DeleteQSMixin, nested_admin.NestedModelAdmin):
    form = AttributeForm
    fields = ('name', 'slug', 'group', 'type_of_value', 'default_str_value')
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('group', 'name', 'type_of_value', 'unit_of_measure', 'fixed_values_list',
                    'default_str_value',)
    list_editable = ('default_str_value',)
    list_display_links = ('group', 'name',)
    list_filter = ('group', 'type_of_value')
    list_select_related = ('group',)
    inlines = (FixedTextValueInline,)
    autocomplete_fields = ('group',)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def get_fields(self, request, obj=None):
        self.obj = obj
        if obj is not None and obj.type_of_value == 2:
            return self.fields + ('unit_of_measure',)
        if obj is not None and obj.type_of_value == 3:
            return self.fields + ('str_true', 'str_false')
        return self.fields

    def get_readonly_fields(self, request, obj=None):
        return ('type_of_value',) if obj is not None else ()

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if not isinstance(inline, FixedTextValueInline) or obj is not None and obj.type_of_value in (4, 5):
                yield inline.get_formset(request, obj), inline

    def delete_queryset(self, request, queryset):
        print(f'{queryset=}')
        updated_product_dict = {}
        first_iter = True
        for obj in queryset:
            keys_to_del = [obj.slug]
            products_to_update = list(Product.objects.filter(categories__groups__attributes=obj))
            remove_keys_in_products_in_qs_deleted_attr(
                keys_to_del, products_to_update, updated_product_dict, first_iter)
            first_iter = False
        Product.objects.bulk_update(updated_product_dict.values(), ['characteristics'])
        queryset.delete()

    def delete_model(self, request, obj):
        if Product.objects.filter(categories__groups__attributes=obj).exists():
            keys_to_del = [obj.slug]
            products_to_update = list(Product.objects.filter(categories__groups__attributes=obj))
            updated_products = remove_keys_in_products(keys_to_del, products_to_update)
            count_prod = Product.objects.bulk_update(updated_products, ['characteristics'])
            self.message_user(
                request, f"Удалены некоторые характеристики для {count_prod} товаров"
            )
        obj.delete()


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    # save_as_continue = True
    pass


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    pass


@admin.register(CombinationOfCategory)
class CombinationOfCategoryAdmin(nested_admin.NestedModelAdmin):
    form = CombinationOfCategoryAdminForm
    filter_horizontal = ('categories',)
    inlines = (GroupPositionInCombinationOfCategoryInLine, MainAttrPositionInCombinationOfCategoryInLine,
               ShotAttrPositionInCombinationOfCategoryInLine)

    class Media:
        css = {
            "all": ("hide_inline_action_admin.css",)
        }


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductSeries)
class ProductSeriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(OtherShop)
admin.site.register(ProductImage)
admin.site.register(Filter)
admin.site.register(ProductSupplierPrice)
