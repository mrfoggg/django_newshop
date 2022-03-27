from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.utils.encoding import force_str

from .models import Attribute, Category, CombinationOfCategory, Group, Product, GroupPositionInCombinationOfCategory, \
    GroupPlacement, MainAttrPositionInCombinationOfCategory, ShotAttrPositionInCombinationOfCategory


def check_doubles_groups(items: list):
    """ в списке состоящем из queryset связанных групп атрибутов различных категорий находим повторяющиеся группы."""
    coincidences_list = set()
    i = 0
    for item_1 in items:
        j = 0
        for item_2 in items:
            if j == i:
                j += 1
                continue
            coincidences = item_1.intersection(item_2)
            if coincidences.exists():
                coincidences_list.update(coincidences)
            j += 1
        i += 1
        if i == len(items):
            break
    if coincidences_list:
        raise ValidationError(
            f"Ошибка, в категориях дублируются группы атрибутов: {', '.join([x.name for x in coincidences_list])}")


def check_change_field_in_fs(formset, field: str) -> bool:
    change = False
    for form in formset.forms:
        if formset.can_delete and formset._should_delete_form(form):
            continue
        if field in form.changed_data:
            change = True
            break
    return change


def get_changes_in_groups_fs(formset):
    deleted_groups_list = []
    added_group_placement_list = [(placement.id, placement.position) for placement in formset.new_objects]
    # print(f'{formset.new_objects[0]=}, {formset.new_objects[0].id=}, , {formset.new_objects[0].position=}')
    for form in formset.forms:
        if form.initial != {}:
            if formset.can_delete and formset._should_delete_form(form):
                deleted_groups_list.append(Group.objects.get(id=form.initial["group"]))
            else:
                if all([form.has_changed, 'group' in form.changed_data,
                        Attribute.objects.filter(group_id=form.initial["group"]).exists()]):
                    deleted_groups_list.append(Group.objects.get(id=form.initial["group"]))
    return deleted_groups_list, [pl[0] for pl in sorted(added_group_placement_list, key=lambda x: x[1])]


def get_added_addict_attr_in_fs(formset):
    added_addict_attr = [(addict_attr.id, addict_attr.position) for addict_attr in formset.new_objects]
    for form in formset.form:
        pass
        # if all([form.initial !={}, ])


def get_changes_in_categories_fs(formset):
    # deleted_categories = [cat_placement.category for cat_placement in formset.deleted_objects] работает некорректно
    # если поле пометить на удаление и поставить новое значениe
    deleted_categories = []
    added_categories_id_list = [cat_placement.category_id for cat_placement in formset.new_objects]
    for form in formset.forms:
        if form.initial != {}:
            if formset.can_delete and formset._should_delete_form(form):
                deleted_categories.append(Category.objects.get(id=form.initial["category"]))
            # данные измений пополняем данными о замененных категориях
            else:
                if form.has_changed and 'category' in form.changed_data:
                    added_categories_id_list.append(form.cleaned_data["category"].id)
                    deleted_categories.append(Category.objects.get(id=form.initial["category"]))
    # все таки нужно вернуть признак добавления категории для корректного запуска update_combination_in_fs_product
    return deleted_categories, added_categories_id_list


def remove_characteristics_keys(product=None, category=None, group=None, attribute=None) -> Product:
    products = []

    def remove_keys_in_products(keys_del, prods):
        for prod in prods:
            print(f'{prod=}')
            print(f'{keys_del=}, {prod.characteristics.keys()=} ')
            total_keys_to_del = set(prod.characteristics.keys()).intersection(set(keys_del))
            if total_keys_to_del:
                list(map(prod.characteristics.pop, total_keys_to_del))
                print('{prod.characteristics=}')
        return prods

    # вариант для случая отвязки товара от категории или замены категории для товара
    if all([product, category, not group]):
        keys_to_del = Attribute.objects.filter(group__categories__in=category).values_list('slug', flat=True)
        remove_keys_in_products(keys_to_del, [products])

    # вариант для случая полного удаления одной или нескольких категорий
    elif all([not product, category, not group]):
        products = list(Product.objects.filter(categories=category))
        keys_to_del = Attribute.objects.filter(group__categories=category).values_list('slug', flat=True)
        remove_keys_in_products(keys_to_del, products)

    # вариант для случая смены групп атрибутов в категории товаров
    elif all([not product, category, group]):
        products = Product.objects.filter(categories=category)
        keys_to_del = Attribute.objects.filter(group__in=group).values_list('slug', flat=True)
        remove_keys_in_products(keys_to_del, products)

    # вариант для случая удаления группы или нескольких групп атрибутов
    elif all([not product, not category, group]):
        print('вариант для случая удаления группы илинескольких групп атрибутов')
        keys_to_del = Attribute.objects.filter(group=group).values_list('slug', flat=True)
        products.extend(remove_keys_in_products(Attribute.objects.filter(group=group).values_list('slug', flat=True),
                                                list(Product.objects.filter(categories__groups=group))))
    else:
        products.extend(remove_keys_in_products(
            [attribute.slug], list(Product.objects.filter(categories__groups__attributes=attribute))))

    return products


def set_prod_pos_to_end(formset, added_categories):
    categories_last_product_positions_dict = {x[0]: x[1] for x in Category.objects.filter(
        id__in=added_categories).annotate(
        last_product_position=Max('productplacement__product_position')).values_list('id', 'last_product_position')}
    for form in formset.forms:
        if (cat_id := form.cleaned_data["category"].id) in added_categories:
            max_position = categories_last_product_positions_dict[cat_id]
            next_product_position = 0 if max_position is None else max_position + 1
            new_placement = form.save(commit=False)
            new_placement.product_position = next_product_position
            new_placement.save()


def create_group_placement_at_end_combination(combinations_with_annotates, sorted_added_group_placement_id_list):
    cc_list_id_with_max_position_group_placement = combinations_with_annotates.values('id', 'max_group_position')
    group_placement_update_list = []
    added_placement_items_with_position_offset = enumerate(sorted_added_group_placement_id_list)
    for cc in cc_list_id_with_max_position_group_placement:
        max_gr_position = 0 if cc['max_group_position'] is None else cc['max_group_position']
        for pos_offset, group_placement_id in added_placement_items_with_position_offset:
            group_placement_placement_in_cc_list_to_create = GroupPositionInCombinationOfCategory(
                combination_of_category_id=cc['id'], group_placement_id=group_placement_id,
                position=max_gr_position + pos_offset)
            group_placement_update_list.append(group_placement_placement_in_cc_list_to_create)
    GroupPositionInCombinationOfCategory.objects.bulk_create(group_placement_update_list)


def create_main_attr_placement_at_end_combination(combinations_with_annotates, added_main_attr_placement_id_list):
    cc_list_id_with_max_position_main_attr = combinations_with_annotates.values('id', 'max_main_attr_position')
    main_attr_placement_update_list = []
    added_main_attr_placement_id_list_with_position_offset = enumerate(added_main_attr_placement_id_list)
    for cc in cc_list_id_with_max_position_main_attr:
        max_main_attr_position = 0 if cc['max_main_attr_position'] is None else cc['max_main_attr_position']
        for pos_offset, main_attr_placement_id in added_main_attr_placement_id_list_with_position_offset:
            group_placement_placement_in_cc_list_to_create = MainAttrPositionInCombinationOfCategory(
                combination_of_category_id=cc['id'], main_attribute_id=main_attr_placement_id,
                position=max_main_attr_position + pos_offset)
            main_attr_placement_update_list.append(group_placement_placement_in_cc_list_to_create)
    MainAttrPositionInCombinationOfCategory.objects.bulk_create(main_attr_placement_update_list)


def create_shot_attr_placement_at_end_combination(combinations_with_annotates, added_shot_attr_placement_id_list):
    cc_list_id_with_max_position_shot_attr = combinations_with_annotates.values('id', 'max_shot_attr_position')
    shot_attr_placement_update_list = []
    added_shot_attr_placement_id_list_with_position_offset = enumerate(added_shot_attr_placement_id_list)
    for cc in cc_list_id_with_max_position_shot_attr:
        max_shot_attr_position = 0 if cc['max_shot_attr_position'] is None else cc['max_shot_attr_position']
        for pos_offset, shot_attr_placement_id in added_shot_attr_placement_id_list_with_position_offset:
            group_placement_placement_in_cc_list_to_create = ShotAttrPositionInCombinationOfCategory(
                combination_of_category_id=cc['id'], shot_attribute_id=shot_attr_placement_id,
                position=max_shot_attr_position + pos_offset)
            shot_attr_placement_update_list.append(group_placement_placement_in_cc_list_to_create)
    ShotAttrPositionInCombinationOfCategory.objects.bulk_create(shot_attr_placement_update_list)


def update_combination_in_fs_product(formset):
    if formset.total_form_count() - len(formset.deleted_forms) > 1:
        combination_of_categories = CombinationOfCategory.objects.annotate(
            cat_id_list=ArrayAgg('categories__id', ordering='categories__id')).filter(
            cat_id_list=sorted(list(formset.instance.categories.values_list('id', flat=True)))).first()
        formset.instance.combination_of_categories = combination_of_categories if combination_of_categories else None
    else:
        formset.instance.combination_of_categories = None


def clean_combination_of_category(category_to_del) -> None:
    """
    принимает экземпляр удаляемой категории товаров и удаляет связаные комбинации категорий которые после удаления:
        - содержат меньше двух категорий;
        - после уменьшения списка категори йдублируется с существующей комбинацией.
    Для товаров которые ссылались на замененныую категорию делает соответсвующиую замену
    """
    related_to_small_combination_id_list = CombinationOfCategory.objects.annotate(
        cnt=Count('categories')).filter(cnt=2, categories=category_to_del).values_list('id', flat=True)
    combinations_without_small_rel = CombinationOfCategory.objects.annotate(
        cat_id_list=ArrayAgg('categories__id', ordering='categories__id')).exclude(
        id__in=related_to_small_combination_id_list)
    combination_to_delete_id_list = list(related_to_small_combination_id_list)

    if combinations_without_small_rel.filter(categories=category_to_del).exists():
        replaced_collection_dict = {}
        for combination in combinations_without_small_rel.filter(categories=category_to_del):
            cat_id_list = combination.cat_id_list
            cat_id_list.remove(category_to_del.id)
            same_combination = combinations_without_small_rel.filter(cat_id_list=cat_id_list)
            if same_combination.exists():
                combination_to_delete_id_list.append(combination.id)
                replaced_collection_dict |= {combination.id: same_combination.first().id}
                Product.objects.filter(combination_of_categories_id=combination.id).update(
                    combination_of_categories_id=same_combination.first().id)
    CombinationOfCategory.objects.filter(id__in=combination_to_delete_id_list).delete()


class DeleteQSMixin:
    def delete_queryset(self, request, queryset):
        if request.POST.get("post"):
            n = 0
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
            request, f"Успешно обновлен набор характеристик для {count_prod} товаров"
        )
