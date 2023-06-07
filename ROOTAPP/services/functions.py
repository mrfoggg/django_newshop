from datetime import datetime

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone

from orders.models import FinanceDocument


def reapply_all_after(obj):
    documents_after = FinanceDocument.objects.filter(person=obj.person, applied__gt=obj.applied, is_active=True)
    print('DOCUMENTS_AFTER - ', documents_after)
    before = obj.balance_after
    docs_to_update = []
    for doc in documents_after:
        doc.balance_after = before + doc.amount
        docs_to_update.append(doc)
        before = doc.balance_after
    FinanceDocument.objects.bulk_update(docs_to_update, ['balance_after'])


def apply_documents(self, request, obj):
    print('APPLY')
    if "_activate" in request.POST or "_reactivate" in request.POST:
        print('_activate')
        msg = 'Проведен датой создания' if "_activate" in request.POST else 'Перепроведен'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = True
        if "_activate" in request.POST:
            obj.applied = timezone.make_aware(datetime.now())
        obj.save()
        reapply_all_after(obj)
        return HttpResponseRedirect(request.path)

    if "_activate_now" in request.POST or "_reactivate_now" in request.POST:
        msg = 'Проведен текущей датой' if "_activate_now" in request.POST else 'Перепроведен текущей датой'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = True
        obj.applied = obj.updated
        obj.save()
        reapply_all_after(obj)
        return HttpResponseRedirect(request.path)

    if "_deactivate" in request.POST:
        msg = 'Проведение документа отмененно'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = False
        reapply_all_after(obj)
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
        obj.save()

    if 'apply_date' in request.POST:
        str_date = request.POST.get('apply_date')
        msg = f'Документ {obj} проведен датой {str_date}'
        self.message_user(request, msg, messages.SUCCESS)
        obj.is_active = True
        date = datetime.strptime(str_date, "%d/%m/%Y %H:%M")
        obj.applied = timezone.make_aware(date)
        obj.save()
        reapply_all_after(obj)
        return HttpResponseRedirect(request.path)
