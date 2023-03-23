from catalog.models import Attribute, Category, FixedTextValue, Group, Product

Category.objects.all().delete()
Group.objects.all().delete()
Product.objects.all().delete()

############################################################
cat_inc = Category.objects.create(name='Инкубаторы')
# _________________________________________________________________________________________
group_box = Group.objects.create(name='Корпус инкубатора')

atr_material = Attribute.objects.create(name="Материал корпуса", slug='material-korpusa', group=group_box, type_of_value=4)
FixedTextValue.objects.create(name='Пенопласт', slug='penoplast', attribute=atr_material)
FixedTextValue.objects.create(name='Пластик', slug='plastic', attribute=atr_material)
FixedTextValue.objects.create(name='Металл', slug='metall', attribute=atr_material)

atr_konstr = Attribute.objects.create(name="Конструкция корпуса", slug='konstruccia-korpusa', group=group_box, type_of_value=4)
FixedTextValue.objects.create(name='Литой', slug='litoj-korpus', attribute=atr_konstr)
FixedTextValue.objects.create(name='Наборной', slug='nabornoj-korpus', attribute=atr_konstr)

# _________________________________________________________________________________________
gr_nagrev = Group.objects.create(name='Нагрев и поддержание температуры')

atr_termik = Attribute.objects.create(name='Тип терморегулятора', slug='tip-termoregulyatora', group=gr_nagrev, type_of_value=4)
FixedTextValue.objects.create(name='Аналоговый терморегулятор', slug='analogovyj-termoregulyator', attribute=atr_termik)
FixedTextValue.objects.create(name='Мембранный терморегулятор', slug='membrannyj-termoregulyator', attribute=atr_termik)
FixedTextValue.objects.create(name='Цифровой терморегулятор', slug='cyfrovoj-termoregulyator', attribute=atr_termik)

atr_power = Attribute.objects.create(name='Мощность нагревателя', slug='moschnost-nagrevatelya', group=gr_nagrev, type_of_value=2)

cat_inc.groups.add(gr_nagrev, group_box)
###########              ###################################################
cat_auto = Category.objects.create(name='Автоматические инкубаторы', parent=cat_inc)

gr_mehanizm = Group.objects.create(name='Параметры механизма поворота')
atr_tip_pov = Attribute.objects.create(name='Тип поворота', slug='tip-povorota', group=gr_mehanizm, type_of_value=4)
FixedTextValue.objects.create(name='Роликовый поворот', slug='rolikovyj-povorot', attribute=atr_tip_pov)
FixedTextValue.objects.create(name='Наклонный поворот', slug='nakloonny-povorot', attribute=atr_tip_pov)
FixedTextValue.objects.create(name='Рамочный поворот', slug='ramochnyj-povorot', attribute=atr_tip_pov)


cat_auto.groups.add(gr_mehanizm)
################           ###########################################
cat_ruki = Category.objects.create(name='Ручные инкубаторы', parent=cat_inc)
# ____________________________________________________________________________________________
gr_ruki = Group.objects.create(name='Параметры рук')

atr_kvo_ruk = Attribute.objects.create(name='Килькость рук', slug='kilkost-ruk', group=gr_ruki, type_of_value=2)
atr_spr = Attribute.objects.create(name='Шпронтность ног', slug='shprotost-nog', group=gr_ruki, type_of_value=1)

cat_ruki.groups.add(gr_ruki)
#================           =============================================================================
cat_meh = Category.objects.create(name='Механические инкубаторы', parent=cat_inc)
cat_meh.groups.add(gr_mehanizm)

t72 = Product.objects.create(name='Инкубатор Теплуша 72 Т')
t72.categories.add(cat_inc)
t72.categories.add(cat_auto)

yo = Product.objects.create(name='Иплуша Ё')
yo.categories.add(cat_inc)
yo.categories.add(cat_ruki)

m = Product.objects.create(name='Иплуша М')
m.categories.add(cat_inc)
m.categories.add(cat_meh)

