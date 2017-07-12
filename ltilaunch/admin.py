import json

from django.contrib import admin
from django.contrib.postgres.fields import JSONField
from django.forms import Widget
from django.utils.safestring import mark_safe

from .models import LTIToolConsumer, LTIToolProvider, LTIToolConsumerGroup, \
    LTIUser


class LTIToolConsumerAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name',
                           'tool_consumer_instance_guid',
                           'description',
                           'match_guid_and_consumer')}),
        ('OAuth', {'fields': ('oauth_consumer_key', 'oauth_consumer_secret')}),
        ('LTI User Matching', {'fields': ('consumer_group',
                                          'matcher_class_name')}))
    exclude = ('recent_nonces',)
    list_display = ('name',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(LTIToolConsumerAdmin, self).get_form(
            request, obj, **kwargs)
        # shorter text fields for keys/guids
        for field in ('tool_consumer_instance_guid',
                      'oauth_consumer_secret',
                      'oauth_consumer_key'):
            form.base_fields[field].widget.attrs['rows'] = 1
        form.base_fields['description'].widget.attrs['rows'] = 2
        return form


class LTIToolProviderAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(LTIToolProviderAdmin, self).get_form(
            request, obj, **kwargs)
        form.base_fields['launch_path'].widget.attrs['rows'] = 1
        return form


class LTILaunchParameterInputs(Widget):
    def render(self, name, value, attrs=None):
        data = json.loads(value) or {}
        ret = '<ul>'
        for k, v in sorted(data.items()):
            ctx = {'key': k,
                   'value': v,
                   'fieldname': name}
            ret += '<li><label style="width: 300px; display: inline-block; ' \
                   'text-align: ' \
                   'right"> ' \
                   '%(key)s</label><input type="hidden" ' \
                   'name="json_key[%(fieldname)s]" value="%(key)s"><input ' \
                   'style="width: 400px" ' \
                   'type="text" ' \
                   'name="json_value[%(' \
                   'fieldname)s]" value="%(value)s"></li>' % ctx
        ret += '</ul>'
        return mark_safe(ret)

    def value_from_datadict(self, data, files, name):
        result = []
        if (('json_key[%s]' % name) in data
                and ('json_value[%s]' % name) in data):
            keys = data.getlist("json_key[%s]" % name)
            values = data.getlist("json_value[%s]" % name)
            for key, value in zip(keys, values):
                if len(key) > 0:
                    result += [(key,value)]
        return json.dumps(dict(result))


class LTIUserAdmin(admin.ModelAdmin):
    list_display = ("person_name", "source_lms",
                    "last_launch_course_id")
    formfield_overrides = {
        JSONField: {'widget': LTILaunchParameterInputs}
    }


admin.site.register(LTIToolConsumer, LTIToolConsumerAdmin)
admin.site.register(LTIToolProvider, LTIToolProviderAdmin)
admin.site.register(LTIToolConsumerGroup, admin.ModelAdmin)
admin.site.register(LTIUser, LTIUserAdmin)