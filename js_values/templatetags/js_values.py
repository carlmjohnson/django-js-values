import json
from datetime import datetime
from numbers import Number

from django import template


register = template.Library()


def contextify(values):
    simplevalues = []
    dates = []
    objs = []
    arrays = []

    for key, value in sorted(values.items()):
        # Make simple values safe for template inclusion with json.dumps
        if (isinstance(value, bool)
            or value is None
            or isinstance(value, Number)
            # For Python 2/3 compatibility, test for a string method
            or hasattr(value, 'startswith')):
            simplevalues.append((key, json.dumps(value)))
        # Special handling for datetimes
        elif isinstance(value, datetime):
            dates.append((key, value.isoformat()))
        # Recurse for dicts/lists
        elif isinstance(value, dict):
            objs.append(key)
            sub_context = contextify({
                '{}.{}'.format(key, inner_key): inner_value
                for (inner_key, inner_value) in value.items()
            })
            simplevalues.extend(sub_context['simplevalues'])
            dates.extend(sub_context['dates'])
            objs.extend(sub_context['objs'])
            arrays.extend(sub_context['arrays'])
        elif isinstance(value, list):
            arrays.append(key)
            sub_context = contextify({
                '{}[{}]'.format(key, i): inner_value
                for (i, inner_value) in enumerate(value)
            })
            simplevalues.extend(sub_context['simplevalues'])
            dates.extend(sub_context['dates'])
            objs.extend(sub_context['objs'])
            arrays.extend(sub_context['arrays'])
        else:
            msg = "Key {!r} has value of unknown type {}".format(key, value)
            raise TypeError(msg)

    return {
        'simplevalues': simplevalues,
        'dates': dates,
        'objs': objs,
        'arrays': arrays,
    }


@register.inclusion_tag('js_values/script.html')
def js_values(values, prefix='window', include_script_tag=True):
    # Normalize prefix to window.WHATEVER
    if not prefix:
        prefix = 'window'

    if not prefix.startswith('window'):
        prefix = 'window.' + prefix

    context = contextify(values)

    context.update({
        'include_script_tag': bool(include_script_tag),
        'prefix': prefix,
    })

    return context
