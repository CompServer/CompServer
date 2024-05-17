# https://github.com/h3/django-colorfield/blob/master/colorfield/widgets.py

from django import forms
from django.conf import settings
from django.conf import settings
from django.forms import TextInput
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

COLORFIELD_HTML_WIDGET = u"""
<script type="text/javascript">(function($){
$(function(){
    var preview = $('<div class="color-picker-preview"><div style="background-color:#%(color)s"></div></div>').insertAfter('#id_%(name)s');
    $('#id_%(name)s').ColorPicker({
        color: '%(color)s',
        onSubmit: function(hsb, hex, rgb, el) { $(el).val(hex); $(el).ColorPickerHide();$(preview).find('div').css('backgroundColor', '#' + hex); },
        onBeforeShow: function () { $(this).ColorPickerSetColor(this.value); },
    }).bind('keyup', function(){ $(this).ColorPickerSetColor(this.value); });
});})(django.jQuery);</script>
"""

class ColorPickerWidget(forms.TextInput):
    """
    A model field widget which implements Stefan Petre's jQuery color picker:
    http://www.eyecon.ro/colorpicker/
    """
    class Media:
        css = {
            'all': (settings.STATIC_URL + 'colorfield/css/colorpicker.css',)
        }
        js = (settings.STATIC_URL + 'colorfield/js/colorpicker.js', )

    def __init__(self, language=None, attrs=None):
        self.language = language or settings.LANGUAGE_CODE[:2]
        super(ColorPickerWidget, self).__init__(attrs=attrs)

    def render(self, name, value, attrs=None, renderer=None):
        rendered = super().render(name, value, attrs, renderer)
        return rendered + mark_safe(COLORFIELD_HTML_WIDGET % {
                            'color': value, 'name': name}) # type: ignore

class ColorWidget(TextInput):
    template_name = "colorfield/color.html"

    class Media:
        if settings.DEBUG:
            js = [
                "colorfield/jscolor/jscolor.js",
                "colorfield/colorfield.js",
            ]
        else:
            js = [
                "colorfield/jscolor/jscolor.min.js",
                "colorfield/colorfield.js",
            ]

    def get_context(self, name, value, attrs=None):
        context = {}
        context.update(self.attrs.copy() or {})
        context.update(attrs or {})
        context.update(
            {
                "widget": self,
                "name": name,
                "value": value,
            }
        )
        if "format" not in context:
            context.update({"format": "hex"})
        return context

    def render(self, name, value, attrs=None, renderer=None):
        return render_to_string(
            self.template_name, self.get_context(name, value, attrs)
        )