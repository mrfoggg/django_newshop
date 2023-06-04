from datetime import datetime

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone


def get_full_name(self):
    last_name = self.last_name if self.last_name else ''
    first_name = self.first_name if self.first_name else ''
    middle_name = self.middle_name if self.middle_name else ''
    return last_name + ' ' + first_name + ' ' + middle_name

def apply_documents(self, request, obj):
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



