from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import ParseError
from rest_framework.serializers import *

from rest_framework_json_api.utils import format_relation_name, get_resource_type_from_instance, \
    get_resource_type_from_serializer


class ResourceIdentifierObjectSerializer(BaseSerializer):
    default_error_messages = {
        'incorrect_model_type': _('Incorrect model type. Expected {model_type}, received {received_type}.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, *args, **kwargs):
        self.model_class = kwargs.pop('model_class', None)
        if 'instance' not in kwargs and not self.model_class:
            raise RuntimeError('ResourceIdentifierObjectsSerializer must be initialized with a model class.')
        super(ResourceIdentifierObjectSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        return {
            'type': format_relation_name(get_resource_type_from_instance(instance)),
            'id': str(instance.pk)
        }

    def to_internal_value(self, data):
        if data['type'] != format_relation_name(self.model_class.__name__):
            self.fail('incorrect_model_type', model_type=self.model_class, received_type=data['type'])
        pk = data['id']
        try:
            return self.model_class.objects.get(pk=pk)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=pk)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data['pk']).__name__)


class SparseFieldsetsMixin(object):
    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        request = context.get('request') if context else None

        if request:
            sparse_fieldset_query_param = 'fields[{}]'.format(get_resource_type_from_serializer(self))
            try:
                param_name = next(key for key in request.query_params if sparse_fieldset_query_param in key)
            except StopIteration:
                pass
            else:
                fieldset = request.query_params.get(param_name).split(',')
                for field_name, field in self.fields.items():
                    if field_name == api_settings.URL_FIELD_NAME:  # leave self link there
                        continue
                    if field_name not in fieldset:
                        self.fields.pop(field_name)

        super(SparseFieldsetsMixin, self).__init__(*args, **kwargs)


class IncludedResourcesValidationMixin(object):
    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        request = context.get('request') if context else None
        view = context.get('view') if context else None

        if request and view:
            include_resources_param = request.query_params.get('include') if request else None
            if include_resources_param:
                included_resources = include_resources_param.split(',')
                for included_field_name in included_resources:
                    if not hasattr(view, 'included_serializers'):
                        raise ParseError('This endpoint does not support the include parameter')
                    if view.included_serializers.get(included_field_name) is None:
                        raise ParseError(
                            'This endpoint does not support the include parameter for field {}'.format(
                                included_field_name
                            )
                        )
        super(IncludedResourcesValidationMixin, self).__init__(*args, **kwargs)


class HyperlinkedModelSerializer(IncludedResourcesValidationMixin, SparseFieldsetsMixin, HyperlinkedModelSerializer):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships instead
    of primary key relationships. Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.

    Included Mixins:
    * A mixin class to enable sparse fieldsets is included
    * A mixin class to enable validation of included resources is included
    """


class ModelSerializer(IncludedResourcesValidationMixin, SparseFieldsetsMixin, ModelSerializer):
    """
    A `ModelSerializer` is just a regular `Serializer`, except that:

    * A set of default fields are automatically populated.
    * A set of default validators are automatically populated.
    * Default `.create()` and `.update()` implementations are provided.

    The process of automatically determining a set of serializer fields
    based on the model fields is reasonably complex, but you almost certainly
    don't need to dig into the implementation.

    If the `ModelSerializer` class *doesn't* generate the set of fields that
    you need you should either declare the extra/differing fields explicitly on
    the serializer class, or simply use a `Serializer` class.


    Included Mixins:
    * A mixin class to enable sparse fieldsets is included
    * A mixin class to enable validation of included resources is included
    """