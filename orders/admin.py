from datetime import datetime

import nested_admin
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
                     ProductInOrder, FinanceDocument, Arrival, ProductMoveItem)


class ProductMoveItemInline(nested_admin.NestedTabularInline):
    formset = ProductMoveItemInlineFormset
    model = ProductMoveItem
    extra = 0


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
    fields = ('product', 'full_current_price_info', 'current_group_price', 'sale_price',
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
    exclude = ('comment',)
    extra = 0
    # sortable_field_name = 'comment'
    inlines = [ProductMoveItemInline, ]
    readonly_fields = ('balance_before', 'amount', 'balance_after')

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
            "all": ('admin/order-admin-changeform.css',)
        }


@admin.register(ClientOrder)
# class ClientOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
class ClientOrderAdmin(nested_admin.NestedModelAdmin, admin.ModelAdmin):
    form = ClientOrderAdminForm
    fieldsets = (
        (
            'Основное',
            {'fields': (
                ('id', 'created', 'updated', 'is_active', 'mark_to_delete',),
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
                       'total_margin')
    list_display = ('id', 'is_active', 'mark_to_delete', 'status', 'payment_type', 'source', '__str__',
                    'contact_person', 'dropper')
    list_display_links = ('__str__',)
    list_editable = ('status', 'is_active', 'mark_to_delete')
    autocomplete_fields = (
        # 'person',
        # 'incoming_phone'
    )
    search_fields = ('person__full_name',)
    inlines = (ProductInClientOrder,)

    class Media:
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js',
            # "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/js/select2.min.js",
            #   'select2.min.js',
            'notyf.min.js',
            'js_functions_for_admin.js', 'order/client_order_admin_form.js',
            'admin/phone_field_select2_customization.js', 'admin/person_field_select2_customization.js')
        css = {'all': ('admin/price_field.css', 'admin/admin-changeform.css', 'select2.min.css', 'notyf.min.css',
                       'order/order-admin-changeform.css')}

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
    list_editable = ('status', )
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
            "all": ('admin/order-admin-changeform.css', 'magnific_popup/magnific-popup.css',
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

    def response_change(self, request, obj):
        rprint('POST - ', request.POST.get('apply_date'))
        if "_create_arrival" in request.POST:
            new_arrival = Arrival(order=obj)
            products_to_create = []
            quantity_dict = dict()
            for pr in obj.products.all():
                if pr.product_id in quantity_dict.keys():
                    if pr.purchase_price.amount in quantity_dict[pr.product_id].keys():
                        quantity_dict[pr.product_id][pr.purchase_price.amount] += pr.quantity
                    else:
                        quantity_dict[pr.product_id][pr.purchase_price.amount] = pr.quantity
                else:
                    quantity_dict[pr.product_id] = {pr.purchase_price.amount: pr.quantity}

            rprint(f'{quantity_dict=}')

            # узанть сколько товаров уже поступило и отнять их
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
            for pr_with_all_prices in quantity_dict.items():
                print('PR_WITH_ALL_PRICES - ', pr_with_all_prices)
                for pr in pr_with_all_prices[1].items():
                    products_to_create.append(
                        ProductMoveItem(
                            product_id=pr_with_all_prices[0], price=Money(pr[0], 'UAH'), quantity=pr[1],
                            document=new_arrival
                        )
                    )
            if len(products_to_create):
                new_arrival.save()
                ProductMoveItem.objects.bulk_create(products_to_create)
            obj.save()
            # return super().response_change(request, obj)
            return HttpResponseRedirect(reverse('admin:orders_arrival_change', args=(new_arrival.id,)))

        if "_activate" in request.POST or "_reactivate" in request.POST:
            msg = 'Проведен датой создания' if "_activate" in request.POST else 'Перепроведен'
            self.message_user(request, msg, messages.SUCCESS)
            obj.is_active = True
            if "_activate" in request.POST:
                obj.applied = obj.created
            obj.save()
            return HttpResponseRedirect(request.path)

        if "_activate_now" in request.POST or "_reactivate_now" in request.POST:
            msg = 'Проведен текущей датой' if "_activate_now" in request.POST else 'Перепроведен текущей датой'
            self.message_user(request, msg, messages.SUCCESS)
            obj.is_active = True
            obj.applied = obj.updated
            obj.save()
            return HttpResponseRedirect(request.path)

        if "_deactivate" in request.POST:
            msg = 'Проведение документа отмененно'
            self.message_user(request, msg, messages.SUCCESS)
            obj.is_active = False
            obj.applied = None
            obj.save()
            return HttpResponseRedirect(request.path)

        if "_un_mark_to_delete" in request.POST:
            obj.mark_to_delete = False
            obj.save()
            return HttpResponseRedirect(request.path)

        if "_mark_to_delete" in request.POST:
            msg = f'Документ {obj} помечен на удаление'
            self.message_user(request, msg, messages.SUCCESS)
            obj.is_active = False
            obj.mark_to_delete = True
            obj.applied = None
            obj.save()

        if 'apply_date' in request.POST:
            str_date = request.POST.get('apply_date')
            msg = f'Документ {obj} проведен датой {str_date}'
            self.message_user(request, msg, messages.SUCCESS)
            obj.is_active = True
            date = datetime.strptime(str_date, "%d/%m/%Y %H:%M")
            obj.applied = timezone.make_aware(date)
            obj.save()
            return HttpResponseRedirect(request.path)

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
    readonly_fields = ('created', 'updated')
    inlines = (ProductMoveItemInline,)


admin.site.register(FinanceDocument)
