from adminsortable2.admin import CustomInlineFormSet
from django import forms
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.forms import NumberInput, TextInput
from .models import (Attribute, Category, CombinationOfCategory, Group, GroupPositionInCombinationOfCategory,
                     MainAttrPositionInCombinationOfCategory, Product, ShotAttrPositionInCombinationOfCategory)
from .services import check_doubles_groups, check_change_field_in_fs


class ProductAttributesWidget(forms.MultiWidget):
    template_name = "product_attribute_widget.html"

    def __init__(self, widgets=None, keys_atr=None):
        self.keys = keys_atr
        super(ProductAttributesWidget, self).__init__(widgets)

    def decompress(self, value):
        keys = self.keys
        # values = []
        # for x in self.keys:
        #     if
        return [value[x] for x in self.keys if x in value.keys()] if value else []

    def value_from_datadict(self, data, files, name):
        value_list = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)
        ]
        return value_list


class ProductAttributesField(forms.MultiValueField):
    def __init__(self, instance, *args, **kwargs):
        list_fields = []
        list_widgets = []
        self.list_keys_attribute = []
        # self.inst = instance

        if instance:
            for group_data in instance.get_sorted_groups:
                atr_count = 0
                attributes_of_group = group_data[1].attributes.order_by('position')
                for attribute in attributes_of_group:
                    atr_count += 1
                    if (atr_type := attribute.type_of_value) == 1:
                        field = forms.CharField(required=False)
                    elif atr_type == 2:
                        field = forms.FloatField(required=False)
                        if attribute.unit_of_measure is not None:
                            attribute.name = f'{attribute.name} ({attribute.unit_of_measure.designation})'
                    elif atr_type == 3:
                        field = forms.BooleanField(required=False)
                    elif atr_type == 4:
                        ch = list(attribute.fixed_values.values_list('slug', 'name'))
                        ch.append([None, '--- Выберите значение ---'])
                        field = forms.ChoiceField(choices=ch, required=False)
                    else:
                        ch = list(attribute.fixed_values.values_list('slug', 'name'))
                        field = forms.MultipleChoiceField(choices=ch, required=False)
                    list_fields.append(field)
                    # field.widget.attrs.update({'label': attribute.name})
                    field.widget.attrs.update({'label': attribute.name, })
                    if len(attributes_of_group) - atr_count == 0:
                        field.widget.attrs.update({'group_end': 'yes'})
                    else:
                        field.widget.attrs.update({'group_end': 'no'})
                    if atr_count == 1:
                        field.widget.attrs.update(
                            {'group_begin': 'yes', 'group_name': group_data[1].name,
                             'category_name': group_data[0]})
                    else:
                        field.widget.attrs.update({'group_begin': 'no'})
                    list_widgets.append(field.widget)
                    self.list_keys_attribute.append(attribute.slug)

        self.widget = ProductAttributesWidget(widgets=list_widgets, keys_atr=self.list_keys_attribute)
        super(ProductAttributesField, self).__init__(fields=list_fields, required=False, require_all_fields=False,
                                                     label='', *args, **kwargs)

    def compress(self, data_list):
        if len(data_list) != 0:
            val = {key: value for key, value in zip(self.list_keys_attribute, data_list)}
        else:
            val = {key: None for key in self.list_keys_attribute}
        return val


class ProductPlacementInlineForProductFS(forms.models.BaseInlineFormSet):
    def duplicate_check(self):
        list_of_query_groups, categories = [], []
        for form in self.forms:
            if 'category' not in form.cleaned_data:
                raise ValidationError('Вы пытаетесь добавить несуществующую категорию')
            if self.can_delete and self._should_delete_form(form):
                continue
            category = form.cleaned_data['category']
            if category in categories:
                raise ValidationError(f"Категория {category} дублируется")
            categories.append(category)
            groups = Group.objects.filter(categories=form.cleaned_data['category'])
            list_of_query_groups.append(groups)
        check_doubles_groups(list_of_query_groups)

    def clean(self):
        super().clean()
        if self.has_changed():
            if check_change_field_in_fs(self, 'category') and (self.total_form_count() - len(self.deleted_forms) > 1):
                self.duplicate_check()


class GroupPlacementInlineFS(CustomInlineFormSet, forms.models.BaseInlineFormSet):
    def clean(self):
        if check_change_field_in_fs(self, "group"):
            groups = []
            for form in self.forms:
                if self.can_delete and self._should_delete_form(form):
                    continue
                print(form.cleaned_data)
                if (group := form.cleaned_data["group"]) in groups:
                    raise ValidationError(f'Группа {group} дублируется')
                groups.append(group)
                for product in Product.objects.filter(categories=self.instance):
                    for category in product.categories.all():
                        if category == self.instance:
                            continue
                        if category.groups.contains(group):
                            raise ValidationError(f'Для товара "{product}" который содержится так же и в категории '
                                                  f'"{category}" группа атрибутов "{group}" уже определена')


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['characteristics'] = ProductAttributesField(instance=self.instance)

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={'size': 90}),
            'length': NumberInput(attrs={'size': 2}),
            'width': NumberInput(attrs={'size': 5}),
            'height': NumberInput(attrs={'size': 3}),
            'length_box': NumberInput(attrs={'size': 5}),
            'width_box': NumberInput(attrs={'size': 3}),
            'height_box': NumberInput(attrs={'size': 5}),
            'weight': NumberInput(attrs={'size': 5}),
            # 'warranty': NumberInput(attrs={'size':5}),
        }


class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={'size': 80}),
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={'size': 80}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={'size': 60}),
        }


class CombinationOfCategoryAdminForm(forms.ModelForm):
    def clean(self):
        super(CombinationOfCategoryAdminForm, self).clean()
        if 'categories' in self.changed_data:
            if len(categories := self.cleaned_data['categories']) < 2:
                raise forms.ValidationError('Коллекция не может состоять менее чем из двух групп')

            check_doubles_groups([category.groups.all() for category in categories])

            if CombinationOfCategory.objects.annotate(cat_id_list=ArrayAgg('categories', ordering=('id',))).filter(
                    cat_id_list=sorted(list(categories.values_list('id', flat=True)))).exists():
                raise forms.ValidationError('Такой набор категорий уже определен')

            init_cat_id_list = sorted([cat.id for cat in self.initial['categories']] if self.instance.id else [])
            new_cat_id_list = sorted(list(categories.values_list('id', flat=True)))

            init_cat_set = set(init_cat_id_list)
            new_cat_set = set(new_cat_id_list)

            added_categories_set = new_cat_set - init_cat_set
            removed_categories = init_cat_set - new_cat_set

            self.save()

            if init_cat_id_list:
                Product.objects.annotate(cat_id_list=ArrayAgg('categories__id', ordering='categories__id')).filter(
                    cat_id_list=init_cat_id_list).update(combination_of_categories=None)

            Product.objects.annotate(cat_id_list=ArrayAgg('categories__id', ordering='categories__id')).filter(
                cat_id_list=new_cat_id_list).update(combination_of_categories=self.instance)

            group_placements_to_add, main_attributes_to_add, shot_attributes_to_add = [], [], []

            next_group_position, next_main_attributes_position, next_shot_attributes_position = 0, 0, 0

            first_category = True
            for category in Category.objects.filter(
                    id__in=added_categories_set).prefetch_related('groupplacement_set', 'main_attributes',
                                                                  'shot_attributes'):
                next_group_position = 0 if first_category else next_group_position
                next_main_attributes_position = 0 if first_category else next_main_attributes_position
                next_shot_attributes_position = 0 if first_category else next_shot_attributes_position
                first_category = False

                for group_placement in category.groupplacement_set.all():
                    group_placements_to_add.append(
                        GroupPositionInCombinationOfCategory(
                            combination_of_category=self.instance,
                            group_placement=group_placement,
                            position=next_group_position
                        )
                    )
                    next_group_position += 1

                for main_attribute in category.main_attributes.all():
                    main_attributes_to_add.append(
                        MainAttrPositionInCombinationOfCategory(
                            combination_of_category=self.instance,
                            main_attribute=main_attribute,
                            position=next_main_attributes_position
                        )
                    )
                    next_main_attributes_position += 1

                for shot_attribute in category.shot_attributes.all():
                    shot_attributes_to_add.append(
                        ShotAttrPositionInCombinationOfCategory(
                            combination_of_category=self.instance,
                            shot_attribute=shot_attribute,
                            position=next_shot_attributes_position
                        )
                    )
                    next_shot_attributes_position += 1

            GroupPositionInCombinationOfCategory.objects.bulk_create(group_placements_to_add)
            GroupPositionInCombinationOfCategory.objects.filter(
                group_placement__category__in=removed_categories).delete()

            MainAttrPositionInCombinationOfCategory.objects.bulk_create(main_attributes_to_add)
            MainAttrPositionInCombinationOfCategory.objects.filter(
                main_attribute__category__in=removed_categories).delete()

            ShotAttrPositionInCombinationOfCategory.objects.bulk_create(shot_attributes_to_add)
            ShotAttrPositionInCombinationOfCategory.objects.filter(
                shot_attribute__category__in=removed_categories).delete()


class GroupPositionInCombinationOfCategoryInLineFS(forms.models.BaseInlineFormSet):
    def clean(self):
        super(GroupPositionInCombinationOfCategoryInLineFS, self).clean()
        for form in self.forms:
            if 'id' not in form.cleaned_data:
                form.can_delete = True
                form.cleaned_data['DELETE'] = True


class MainAttrPositionInCombinationOfCategoryInLineFS(forms.models.BaseInlineFormSet):
    def clean(self):
        super(MainAttrPositionInCombinationOfCategoryInLineFS, self).clean()
        for form in self.forms:
            if 'id' not in form.cleaned_data:
                form.can_delete = True
                form.cleaned_data['DELETE'] = True


class ShotAttrPositionInCombinationOfCategoryInLineFS(forms.models.BaseInlineFormSet):
    def clean(self):
        super(ShotAttrPositionInCombinationOfCategoryInLineFS, self).clean()
        for form in self.forms:
            if 'id' not in form.cleaned_data:
                form.can_delete = True
                form.cleaned_data['DELETE'] = True
