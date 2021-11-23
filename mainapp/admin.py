from PIL import Image

from django.contrib import admin
from django.db import reset_queries
from django.forms import ModelChoiceField, ModelForm
from django.utils.safestring import mark_safe

# Register your models here.
from .models import *


class SmartphoneAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        if not instance:
            self.fields['sd_volume_max'].widget.attrs.update({
                'readonly': True,
                'style': 'background: lightgray;',
            })

    # Метод для работы с полями
    def clean(self):
        if not self.cleaned_data['sd']:
            self.cleaned_data['sd_volume_max'] = None
        
        return self.cleaned_data



class NotebookAdminForm(ModelForm):

    # Что у загруженного изображения минимальная длина и ширина
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            '<span style="color:red; font-size:14px">При загрузке изображения с разрешением больше {}x{} оно будет обрезано</span>'.format(
                *Product.MAX_RESOLUTION
                )
            )


class NotebookAdmin(admin.ModelAdmin):

    form = NotebookAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='notebooks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SmartphoneAdmin(admin.ModelAdmin):

    change_form_template = 'admin.html'
    form = SmartphoneAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='smartphones'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


"""Тут собраны основные формы и модели из админки"""
class FictionBookAdminForm(ModelForm):

    # Что у загруженного изображения минимальная длина и ширина
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            '<span style="color:red; font-size:14px">При загрузке изображения с разрешением больше {}x{} оно будет обрезано</span>'.format(
                *Product.MAX_RESOLUTION
                )
            )


class ScienceBookAdminForm(ModelForm):
    # Что у загруженного изображения минимальная длина и ширина
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            '<span style="color:red; font-size:14px">При загрузке изображения с разрешением больше {}x{} оно будет обрезано</span>'.format(
                *Product.MAX_RESOLUTION
                )
            )


class FictionBookAdmin(admin.ModelAdmin):

    change_form_template = 'admin.html'
    form = FictionBookAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='fictionbooks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ScienceBookAdmin(admin.ModelAdmin):

    change_form_template = 'admin.html'
    form = ScienceBookAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='sciencebooks'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(FictionBook, FictionBookAdmin)
admin.site.register(ScienceBook, ScienceBookAdmin)

admin.site.register(Cart) 
admin.site.register(Category) 
admin.site.register(Cartproduct) 
admin.site.register(Customer) 
admin.site.register(Order)