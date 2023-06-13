from datetime import datetime

import nested_admin
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from djmoney.money import Money
# import rprint as rprint
from rich import print as rprint
from django import forms
from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models
from djmoney.forms import MoneyField
from polymorphic.admin import StackedPolymorphicInline, PolymorphicInlineSupportMixin

from ROOTAPP.models import Person, Phone, PriceTypePersonBuyer
from Shop_DJ import settings
from catalog.models import ProductSupplierPriceInfo
from finance.admin_forms import money_widget_only_uah
from .admin_form import ClientOrderAdminForm, ProductInClientOrderAdminInlineForm, ProductMoveItemInlineFormset
from .models import (BY_ONECLICK_STATUSES_CLIENT_DISPLAY, ByOneclick,
                     ByOneclickPersonalComment, OneClickUserSectionComment, ClientOrder, SupplierOrder, Realization,
                     ProductInOrder, FinanceDocument, Arrival, ProductMoveItem, apply_documents, reapply_all_after)


class ProductMoveItemInline(nested_admin.NestedTabularInline):
    formset = ProductMoveItemInlineFormset
    readonly_fields = ('quantity_before', 'quantity_after')
    model = ProductMoveItem
    extra = 0


class ProductMoveItemInlineReadonly(nested_admin.NestedTabularInline):
    model = ProductMoveItem

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class ByOneclickCommentAdminInline(admin.TabularInline):
    model = ByOneclickPersonalComment
    extra = 1
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': '1'})}
    }


class OneClickUserSectionCommentInline(admin.TabularInline):
    model = OneClickUserSectionComment
    readonly_fields = ('comment_type', 'description', 'created')
    extra = 0
    max_num = 0


class ProductInClientOrder(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    form = ProductInClientOrderAdminInlineForm
    fields = ('product', 'drop_realization', 'full_current_price_info', 'current_group_price', 'sale_price',
              'drop_price',
              'quantity', 'sale_total', 'margin', 'margin_total',
              'margin_percent', 'profitability',
              'supplier_order', 'supplier_price_variants',
              'purchase_price', 'client_order_position', 'purchase_total')
    readonly_fields = (
        'full_current_price_info', 'sale_total', 'purchase_total', 'margin', 'margin_total', 'margin_percent',
        'profitability', 'current_group_price'
    )
    model = ProductInOrder
    extra = 0
    sortable_field_name = 'client_order_position'
    verbose_name = 'Товар в заказе'
    verbose_name_plural = 'Товары в заказе'

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(ProductInClientOrder, self).get_formset(request, obj, **kwargs)
        self.form.request = request
        return formset

    def formfield_for_dbfield(self, db_field, **kwargs):
        # This method will turn all TextFields into giant TextFields
        if db_field.name == 'quantity':
            return forms.CharField(widget=forms.widgets.NumberInput(attrs={'size': 4, }), initial=1)
        if db_field.name in ('sale_price', 'purchase_price', 'drop_price'):
            return MoneyField(required=False, widget=money_widget_only_uah)
        return super().formfield_for_dbfield(db_field, **kwargs)


class ProductInSupplierOrder(nested_admin.SortableHiddenMixin, nested_admin.NestedTabularInline):
    # adminsortable2 требует fields именно списком
    fields = ('product', 'purchase_price', 'quantity', 'client_order', 'supplier_order_position', 'arrive_quantity')
    readonly_fields = ('arrive_quantity',)

    model = ProductInOrder
    extra = 2
    autocomplete_fields = ('product', 'client_order')
    sortable_field_name = 'supplier_order_position'
    verbose_name = 'Товар в заказе'
    verbose_name_plural = 'Товары в заказе'
    extra = 0


class ArrivalInline(nested_admin.NestedTabularInline):
    model = Arrival
    fields = ('is_active', 'mark_to_delete', 'applied', 'comment',
              'balance_before', 'amount', 'balance_after')
    extra = 0
    readonly_fields = ('balance_before',)
    # sortable_field_name = 'comment'
    inlines = [ProductMoveItemInlineReadonly, ]
    show_change_link = True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class ByOneclickAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person'].queryset = Person.objects.filter(phones__phone=self.instance.phone)

    def clean(self):
        if 'status' in self.changed_data:
            new_user_comment = OneClickUserSectionComment(
                order=self.instance, comment_type=1,
                description=BY_ONECLICK_STATUSES_CLIENT_DISPLAY[self.cleaned_data["status"]])
            new_user_comment.save()
            self.instance.is_active = False if self.cleaned_data['status'] in [4, 5, 7] else True
        self.save()


@admin.register(ByOneclick)
class ByOneclickAdmin(admin.ModelAdmin):
    form = ByOneclickAdminForm

    fields = (
        ('product', 'price',),
        ('phone', 'is_active'),
        ('created', 'updated'),
        ('person', 'this_number_contacts'),
        ('status', 'extend_status'),
        ('session_key', 'this_session_oneclicks'),
        'user_ip_info'
    )
    list_display = ('id', 'created', 'phone', 'is_active', 'status', 'product', 'this_number_contacts')
    list_display_links = ('created', 'phone')
    readonly_fields = ('phone', 'created', 'updated', 'this_number_contacts', 'price', 'is_active', 'session_key',
                       'this_session_oneclicks', 'user_ip_info')
    inlines = (ByOneclickCommentAdminInline, OneClickUserSectionCommentInline)

    class Media:
        js = ('admin/textarea-autoheight.js',)
        css = {
            "all": ('admin/admin-changeform.css',)
        }


@admin.register(ClientOrder)
# class ClientOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
class ClientOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
    form = ClientOrderAdminForm
    fieldsets = (
        (
            'Основное',
            {'fields': (
                ('id', 'created', 'updated', 'applied'),
                ('is_active', 'mark_to_delete'),
                ('status', 'extend_status'), ('source', 'payment_type'),
            )},
        ),
        (
            'Контактная информация',
            {'fields': (
                ('person', 'incoming_phone',),
            )}
        ),
        (
            'Опт',
            {'fields': (
                ('dropper', 'group_price_type',),
            )}
        ),
        (
            'Доставка',
            {'fields': (
                ('address',), ('contact_person', 'delivery_phone')
            )}
        ),
        (
            'Итого по заказу',
            {'fields': (
                ('total_quantity', 'total_amount', 'total_purchase_amount', 'total_margin'),
            )}
        ),
    )
    readonly_fields = ('id', 'created', 'updated', 'total_quantity', 'total_amount', 'total_purchase_amount',
                       'total_margin', 'is_active', 'mark_to_delete', 'applied')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', 'payment_type', 'source', '__str__',
                    'contact_person', 'dropper')
    list_display_links = ('__str__',)
    list_editable = ('status',)
    autocomplete_fields = (
        # 'person',
        # 'incoming_phone'
    )
    search_fields = ('person__full_name',)
    inlines = (ProductInClientOrder,)

    change_form_template = "client_order_changeform.html"

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            # "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/js/select2.min.js",
            'select2.min.js',
            'magnific_popup/jquery.magnific-popup.min.js',
            'jquery.datetimepicker.full.min.js',
            'notyf.min.js',
            'js_functions_for_admin.js', 'order/client_order_admin_form.js',
            'admin/phone_field_select2_customization.js', 'admin/person_field_select2_customization.js',
            'admin/apply_documents.js')
        css = {'all': ('admin/price_field.css', 'admin/admin-changeform.css', 'select2.min.css', 'notyf.min.css',
                       'order/order-admin-changeform.css', 'magnific_popup/magnific-popup.css',
                       'jquery.datetimepicker.min.css')}

    # для отображения только активных товаров
    def get_search_results(self, request, queryset, search_term):
        print('GET_SEARCH_RESULTS')
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
        print('search_term -', search_term)
        if 'model_name' in request.GET.keys():
            print('MODEL_NAME - ', request.GET['model_name'])
            if request.GET['model_name'] == 'productinorder':
                queryset = queryset.filter(is_active=True, mark_to_delete=False)
        return queryset, may_have_duplicates

    def get_form(self, request, obj=None, **kwargs):
        print('GET PARENT FORM')
        self._request_method = request.method
        self._curent_phone_ = obj.incoming_phone if obj else None
        self._curent_person_ = obj.person if obj else None
        self._curent_dropper_ = obj.dropper if obj else None
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if hasattr(self, '_request_method'):
            phone = self._curent_phone_ if hasattr(self, '_curent_phone_') else None
            person_id = self._curent_person_.id if hasattr(self, '_curent_person_') and self._curent_person_ else None
            dropper_id = self._curent_dropper_.id if hasattr(self,
                                                             '_curent_dropper_') and self._curent_dropper_ else None
            if db_field.name == "incoming_phone" and self._request_method == 'GET':
                kwargs["queryset"] = Phone.objects.filter(id=phone.id) if phone else Phone.objects.none()
            if db_field.name == "person" and self._request_method == 'GET':
                kwargs["queryset"] = Person.objects.filter(id=person_id) if person_id else Person.objects.none()
            if db_field.name == "group_price_type" and self._request_method == 'GET':
                kwargs["queryset"] = PriceTypePersonBuyer.objects.filter(person_id=dropper_id) if dropper_id \
                    else PriceTypePersonBuyer.objects.filter(person_id=person_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def response_change(self, request, obj):
        apply_result = apply_documents(self, request, obj)
        if apply_result:
            return apply_result
        return super().response_change(request, obj)

    baton_form_includes = [
        ('order/admin_order_ajax_urls.html', 'id', 'top',),
        ('admin/include_select2.html', 'id', 'top',),
        ('order/person_phones.html', 'person', 'bottom',),
        ('order/founded_persons.html', 'incoming_phone', 'bottom',),
    ]


@admin.register(SupplierOrder)
class SupplierOrderAdmin(nested_admin.NestedModelAdmin):
    fields = (
        ('id', 'is_active', 'mark_to_delete', 'status', 'stock'),
        ('created', 'updated', 'applied'),
        ('person', 'price_type'), 'comment'
    )
    readonly_fields = ('id', 'created', 'updated', 'applied', 'is_active', 'mark_to_delete')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', '__str__')
    list_display_links = ('__str__',)
    list_editable = ('status',)
    search_fields = ('person__last_name',)
    inlines = (
        ProductInSupplierOrder,
        ArrivalInline
    )
    change_form_template = "supplier_order_changeform.html"

    class Media:
        js = ('admin/textarea-autoheight.js',
              # 'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
              # jquery.js от datetimepicker
              # 'jquery.js',
              'magnific_popup/jquery.magnific-popup.min.js',
              'jquery.datetimepicker.full.min.js',
              'admin/apply_documents.js')
        css = {
            "all": ('admin/admin-changeform.css', 'magnific_popup/magnific-popup.css',
                    'jquery.datetimepicker.min.css')
        }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'person':
            kwargs["queryset"] = Person.objects.filter(is_supplier=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term, )
        if 'model_name' in request.GET.keys():
            if request.GET['model_name'] == 'productinorder':
                queryset = queryset.filter(is_active=True, mark_to_delete=False)
        return queryset, may_have_duplicates

    # def save_related(self, request, form, formsets, change):
    #     for form in formsets[0]:
    #         print('FORM - ', form)
    #     formsets[0].save()

    def response_change(self, request, obj):
        rprint('POST - ', request.POST.get('apply_date'))
        if "_create_arrival" in request.POST:
            if not obj.stock:
                msg = 'Товары не получены. Не указан склад'
                self.message_user(request, msg, messages.ERROR)
            else:
                new_arrival = Arrival(
                    order=obj, person=obj.person, stock=obj.stock, is_active=True,
                    applied=timezone.make_aware(datetime.now())
                )
                products_to_create = []
                quantity_dict = dict()
                for pr in obj.products.all():
                    if pr.product_id in quantity_dict.keys():
                        # quantity_dict[pr.product_id]['total'] += pr.quantity
                        if pr.purchase_price.amount in quantity_dict[pr.product_id].keys():
                            quantity_dict[pr.product_id][pr.purchase_price.amount] += pr.quantity
                        else:
                            quantity_dict[pr.product_id][pr.purchase_price.amount] = pr.quantity
                    else:
                        quantity_dict[pr.product_id] = {
                            pr.purchase_price.amount: pr.quantity,
                            # 'total': pr.quantity
                        }

                rprint(f'{quantity_dict=}')

                # узанть сколько товаров уже поступило и отнять их.
                for ar in Arrival.objects.filter(order=obj):
                    for p in ar.productmoveitem_set.all():
                        if p.product_id in quantity_dict.keys():
                            while p.quantity:
                                if p.price.amount in quantity_dict[p.product_id].keys():
                                    quantity_in_order = quantity_dict[p.product_id][p.price.amount]
                                    if p.quantity >= quantity_in_order:
                                        quantity_dict[p.product_id].pop(p.price.amount)
                                        if not quantity_dict[p.product_id]:
                                            quantity_dict.pop(p.product_id)
                                            p.quantity = 0
                                            quantity_in_order = 0
                                        if p.quantity > quantity_in_order:
                                            new_price_amount = list(quantity_dict[p.product_id].keys())[0]
                                            p.price.amount = new_price_amount
                                        p.quantity -= quantity_in_order
                                    else:
                                        quantity_dict[p.product_id][p.price.amount] = quantity_in_order - p.quantity
                                        p.quantity = 0
                                else:
                                    new_price_amount = list(quantity_dict[p.product_id].keys())[0]
                                    p.price.amount = new_price_amount
                rprint('NEW quantity_dict = ', quantity_dict)

                # создаем поступление для еще не поступивших товаров
                total_amount = Money(0, 'UAH')
                quantity_after_dict = dict()
                for pr_with_all_prices in quantity_dict.items():
                    print('PR_WITH_ALL_PRICES - ', pr_with_all_prices)
                    for pr in pr_with_all_prices[1].items():
                        item_before = ProductMoveItem.objects.filter(
                            product_id=(pr_id := pr_with_all_prices[0]), quantity_after__has_key=str(obj.stock_id)
                        )
                        quantity_before = quantity_after_dict[pr_id] \
                            if pr_id in quantity_after_dict.keys() \
                            else item_before.order_by('document__applied').last().quantity_after[str(obj.stock_id)] \
                            if item_before.exists() else 0

                        total_amount += (price := Money(pr[0], 'UAH')) * (quantity := pr[1])

                        quantity_after = quantity_before + quantity
                        quantity_after_dict[pr_id] = quantity_after
                        print('PRICE', price)
                        print('quantity', quantity)
                        new_product_move_item = ProductMoveItem(
                            product_id=pr_with_all_prices[0], price=price, quantity=quantity,
                            document=new_arrival
                        )
                        new_product_move_item.quantity_after[obj.stock_id] = quantity_after
                        new_product_move_item.quantity_before[obj.stock_id] = quantity_before
                        products_to_create.append(new_product_move_item)
                if len(products_to_create):
                    new_arrival.amount = total_amount
                    new_arrival.save()
                    ProductMoveItem.objects.bulk_create(products_to_create)
                obj.save()
                # return super().response_change(request, obj)
                msg = 'Товары получены на склад - ' + obj.stock.__str__()
                self.message_user(request, msg, messages.SUCCESS)
                return HttpResponseRedirect(reverse('admin:orders_arrival_change', args=(new_arrival.id,)))
        apply_result = apply_documents(self, request, obj)
        if apply_result:
            return apply_result

        return super().response_change(request, obj)


@admin.register(Realization)
class RealizationAdmin(admin.ModelAdmin):
    fields = (
        ('id', 'is_active', 'mark_to_delete', 'status',),
    )
    readonly_fields = ('id', 'created', 'updated')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', '__str__')
    list_display_links = ('__str__',)
    list_editable = ('status', 'is_active', 'mark_to_delete')


@admin.register(Arrival)
class ArrivalAdmin(nested_admin.NestedModelAdmin):
    fields = ('id', 'person', ('order', 'stock'), ('is_active', 'mark_to_delete'),
              ('created', 'updated', 'applied'), ('balance_before', 'amount', 'balance_after'))
    readonly_fields = ('created', 'updated', 'applied', 'is_active', 'mark_to_delete', 'balance_before', 'amount',
                       'balance_after', 'id')
    list_display = ('id', 'applied', 'person', 'stock', 'is_active', 'mark_to_delete', 'balance_before', 'amount',
                    'balance_after')
    list_filter = ('stock',)
    autocomplete_fields = ('person',)
    inlines = (ProductMoveItemInline,)

    change_form_template = 'admin/apply_buttons.html'

    def save_related(self, request, form, formsets, change):
        # print('form changed_data - ', form.changed_data)
        # print('form cleaned_data - ', form.cleaned_data)
        formset = formsets[0]
        new_amount = 0
        is_changed_total_amount = False
        print('OBJ - ', form.instance)
        total_amount = 0
        for formset_form in formset.forms:
            print('formset_form changed_data - ', formset_form.changed_data)
            print('formset_form cleaned_data - ', formset_form.cleaned_data)
            # print('formset_form data - ', formset_form.data)
            print('=' * 40)

            if formset.can_delete and formset._should_delete_form(formset_form):
                pass
                # пересчитать айтемы после
                # пересчитать сумму документа
                is_changed_total_amount = True

            else:
                total_amount += formset_form.cleaned_data['quantity'] * formset_form.cleaned_data['price']
                changed_data = formset_form.changed_data
                if 'product' in formset_form.changed_data or 'quantity' in formset_form.changed_data or 'stock' in form.changed_data:
                    pass
                    # пересчитать этот айтем
                    if form.instance.is_active:
                        pass
                        # пересчитать айтемы после
                if 'is_active' in form.changed_data:
                    pass
                    # пересчитать айтемы после
                if 'arrived' in form.changed_data:
                    pass
                    # пересчитать айтемы после с учетом более ранней даты
                if 'quantity' in formset_form.changed_data or 'price' in formset_form.changed_data:
                    pass
                    # пересчитать сумму документа
                    is_changed_total_amount = True
        print('is_changed_total_amount - ', is_changed_total_amount)
        if is_changed_total_amount:
            print('RESET TOTALAMOUNT', total_amount)
            form.instance.amount = total_amount
            reapply_all_after(form.instance, form.instance.applied)

        formsets[0].save()

    def response_change(self, request, obj):
        apply_result = apply_documents(self, request, obj)
        if apply_result:
            return apply_result
        return super().response_change(request, obj)

    class Media:
        css = {"all": (
            'admin/admin-changeform.css',
            'magnific_popup/magnific-popup.css',
            'jquery.datetimepicker.min.css')}
        js = (

            'admin/jq.js',
            'magnific_popup/jquery.magnific-popup.min.js',
            'jquery.datetimepicker.full.min.js',
            'admin/apply_documents.js', 'admin/textarea-autoheight.js',
        )


admin.site.register(FinanceDocument)
