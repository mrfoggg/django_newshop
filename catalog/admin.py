import copy
import nested_admin
from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_str
from django_summernote.admin import SummernoteModelAdmin
from mptt.admin import DraggableMPTTAdmin
from .admin_forms import (CombinationOfCategoryAdminForm, GroupPlacementInlineFS,
                          GroupPositionInCombinationOfCategoryInLineFS,
                          MainAttrPositionInCombinationOfCategoryInLineFS, ProductForm,
                          ProductPlacementInlineForProductFS, ShotAttrPositionInCombinationOfCategoryInLineFS)
from .models import (Attribute, Category, CombinationOfCategory, FixedTextValue, Group, GroupPlacement,
                     GroupPositionInCombinationOfCategory, MainAttribute, MainAttrPositionInCombinationOfCategory,
                     Product, ProductPlacement, ShotAttribute, ShotAttrPositionInCombinationOfCategory, UnitOfMeasure)
from .services import (clean_combination_of_category, remove_characteristics_keys,
                       get_changes_in_categories_fs, get_changes_in_groups_fs,
                       update_combination_in_fs_product, set_prod_pos_to_end, create_group_placement_at_end_combination,
                       DeleteQSMixin, create_main_attr_placement_at_end_combination)

from django.core import serializers
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _, gettext_lazy
from django.template.response import TemplateResponse


@admin.action(description='Сериализовать')
def export_as_json(modeladmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    serializers.serialize("json", queryset, stream=response)
    return response


class ProductPlacementInlineForCategory(nested_admin.NestedTabularInline):
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


class GroupPlacementInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    formset = GroupPlacementInlineFS
    readonly_fields = ('attributes_list',)
    model = GroupPlacement
    extra = 0
    fields = ('group', 'attributes_list', 'position')
    sortable_field_name = 'position'
    ordering = ('position',)

    @admin.display(description='Содержжит атрибуты')
    def attributes_list(self, obj):
        return obj.group.attributes_list


class AttributeInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = Attribute
    readonly_fields = ('name', 'type_of_value', 'unit_of_measure', 'fixed_values_list',)
    fields = ('name', 'type_of_value', 'unit_of_measure', 'fixed_values_list', 'display_when_value_none', 'position')
    show_change_link = True
    extra = 0


class FixedTextValueInline(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = FixedTextValue
    prepopulated_fields = {"slug": ("name",)}
    extra = 0


class GroupPositionInCombinationOfCategoryInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    extra = 0
    readonly_fields = ('group_placement',)
    formset = GroupPositionInCombinationOfCategoryInLineFS
    model = GroupPositionInCombinationOfCategory
    # can_delete = False


class MainAttributeInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = MainAttribute
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = Attribute.objects.filter(group_id__in=request._obj_)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ShotAttributeInLine(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    model = ShotAttribute
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = Attribute.objects.filter(group_id__in=request._obj_)
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


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin, nested_admin.NestedModelAdmin):
    list_display = ('tree_actions', 'indented_title', 'groups_list',)
    prepopulated_fields = {"slug": ("name",)}
    save_as = True
    save_as_continue = False
    inlines = (GroupPlacementInline, MainAttributeInLine, ShotAttributeInLine, ProductPlacementInlineForCategory)
    actions = [export_as_json]

    class Media:
        css = {
            "all": ("category_admin.css",)
        }

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            request._obj_ = GroupPlacement.objects.filter(category_id=obj.id).values_list('group_id', flat=True)
        else:
            request._obj_ = []
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
        if obj.productplacement_set.exists() and obj.groups.attributes.exists():
            products_to_update = remove_characteristics_keys(category=obj)
            if once_del:
                print(f'{products_to_update=}')
                count_prod = Product.objects.bulk_update(products_to_update, ['characteristics'])
                self.message_user(
                    request, f"Удалены некоторые характеристики для {count_prod} товаров"
                )
        obj.delete()
        return products_to_update

    def save_related(self, request, form, formsets, change):
        # for fs_with_order in enumerate(formsets):
        #     fs_with_order[1].save()
        #     if fs_with_order[0] == 0:
        #         group_fs = fs_with_order[1]
        #         deleted_groups_list, added_group_placement_list = get_changes_in_groups_fs(group_fs)
        #         if added_group_placement_list:
        #             create_group_placement_at_end_combination(group_fs.instance, added_group_placement_list)

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

        combinations = CombinationOfCategory.objects.filter(categories=(category := groups_fs.instance))
        if sorted_added_group_placement_id_list:
            combinations = combinations.annotate(max_group_position=Max('group_position__position'))
        if added_main_attr_placement_id_list:
            combinations = combinations.annotate(max_main_attr_position=Max('main_attr_positions__position'))
        if added_shot_attr_placement_id_list:
            combinations = combinations.annotate(max_shot_attr_position=Max('shot_attr_positions_position'))
        comb = combinations.first()

        if sorted_added_group_placement_id_list:
            create_group_placement_at_end_combination(combinations, sorted_added_group_placement_id_list)

        # create_main_attr_placement_at_end_combination(main_attr_fs)

        if deleted_groups_list:
            products_to_update = remove_characteristics_keys(category=groups_fs.instance, group=deleted_groups_list)
            Product.objects.bulk_update(products_to_update, ['characteristics'])


@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin, SummernoteModelAdmin):
    form = ProductForm
    fields = ['name', 'slug', 'admin_category', 'characteristics', 'combination_of_categories']
    list_display = ('name', 'category_placement')
    prepopulated_fields = {"slug": ("name",)}
    save_on_top = True
    inlines = (ProductPlacementInlineForProduct,)
    # formfield_overrides = {
    #     models.JSONField: {'widget': JSONEditorWidget},
    # }
    readonly_fields = ('get_sorted_groups', 'combination_of_categories')
    summernote_fields = ('description',)
    change_form_template = "product_changeform.html"
    actions = [export_as_json]

    def save_related(self, request, form, formsets, change):
        # сохраняем FormSet иначе 'ProductPlacementFormFormSet' object has no attribute 'deleted_objects'
        category_fs = formsets[0]
        category_fs.save()
        deleted_categories_list, added_categories_id_list = get_changes_in_categories_fs(category_fs)

        if added_categories_id_list:
            set_prod_pos_to_end(category_fs, added_categories_id_list)

        if deleted_categories_list:
            remove_characteristics_keys(product=category_fs.instance, category=deleted_categories_list)

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
            related_categories_product_pos = {x[0]: x[1] for x in Category.objects.annotate(last_product_position=Max(
                'productplacement__product_position')).filter(
                productplacement__product=obj).values_list('id', 'last_product_position')}
            print(related_categories_product_pos)
            placements_to_create = [
                ProductPlacement(
                    product=product_copy, category_id=cat, product_position=related_categories_product_pos[cat] + 1)
                for cat, pos in related_categories_product_pos.items()]
            ProductPlacement.objects.bulk_create(placements_to_create)
            return HttpResponseRedirect(reverse('admin:catalog_product_change', args=(product_copy.id,)))
        return super().response_change(request, obj)


@admin.register(Group)
class GroupAdmin(DeleteQSMixin, nested_admin.NestedModelAdmin, ):
    list_display = ('name', 'attributes_list')
    inlines = (AttributeInline,)

    class Media:
        css = {
            "all": ("hide_inline_action_admin.css",)
        }

    def delete_model(self, request, obj, once_del=True):
        products_to_update = None
        if obj.attributes.exists() and Product.objects.filter(categories__groups=obj).exists():
            products_to_update = remove_characteristics_keys(group=obj)
            if once_del:
                count_prod = Product.objects.bulk_update(products_to_update, ['characteristics'])
                self.message_user(
                    request, f"Удалены некоторые характеристики для {count_prod} товаров"
                )
        obj.delete()
        return products_to_update


@admin.register(Attribute)
class AttributeAdmin(DeleteQSMixin, nested_admin.NestedModelAdmin):
    fields = ('name', 'slug', 'group', 'type_of_value', 'display_when_value_none')
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('group', 'name', 'type_of_value', 'unit_of_measure', 'fixed_values_list',
                    'display_when_value_none',)
    list_editable = ('display_when_value_none',)
    list_display_links = ('group', 'name',)
    list_filter = ('group', 'type_of_value')
    list_select_related = ('group',)
    inlines = (FixedTextValueInline,)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.obj = None

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "type_of_value":
            if self.obj:
                if self.obj.type_of_value == 4:
                    kwargs['choices'] = (
                        (4, "Вариант из фикс. значений"),
                        (5, "Набор фикс. значений")
                    )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_fields(self, request, obj=None):
        self.obj = obj
        return self.fields + ('unit_of_measure',) if obj is not None and obj.type_of_value == 2 else self.fields

    def get_readonly_fields(self, request, obj=None):
        return ('type_of_value',) if obj is not None and obj.type_of_value != 4 else ()

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if not isinstance(inline, FixedTextValueInline) or obj is not None and obj.type_of_value in (4, 5):
                yield inline.get_formset(request, obj), inline

    def delete_model(self, request, obj, once_del=True):
        products_to_update = None
        if Product.objects.filter(categories__groups__attributes=obj).exists():
            products_to_update = remove_characteristics_keys(attribute=obj)
            if once_del:
                count_prod = Product.objects.bulk_update(products_to_update, ['characteristics'])
                self.message_user(
                    request, f"Удалены некоторые характеристики для {count_prod} товаров"
                )
        obj.delete()
        return products_to_update


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    pass


@admin.register(CombinationOfCategory)
class CombinationOfCategoryAdmin(nested_admin.NestedModelAdmin):
    form = CombinationOfCategoryAdminForm
    inlines = (GroupPositionInCombinationOfCategoryInLine, MainAttrPositionInCombinationOfCategoryInLine,
               ShotAttrPositionInCombinationOfCategoryInLine)

    class Media:
        css = {
            "all": ("hide_inline_action_admin.css",)
        }
