from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_form_fields(form, *fields):
    if fields:
        # preserve order
        rendered_values = [render_field(form[field]) for field in fields]
    else:
        rendered_values = [render_field(form[field]) for field in form.fields]
    return mark_safe("".join(rendered_values))


@register.filter
def dict_lookup(dictionary, key):
    return dictionary.get(key, None)


@register.simple_tag
def render_field(form_field, **attrs):
    render_function = {
        "select": render_select_input,
        "checkbox": render_checkbox_input,
    }.get(form_field.widget_type, render_text_input)
    return render_function(form_field, **attrs)


@register.simple_tag
def render_text_input(form_field, **attrs):
    TEXT_INPUT_TEMPLATE = """
    <div class="form-control w-full" {% include "generic/attrs.html" with attrs=control_attrs %}>
      <label class="label font-bold" for="{{ form_field.id_for_label }}">{{ form_field.label }}</label>
      {{ form_field }}
      <small class="form-text text-muted">{{ form_field.help_text|safe }}</small>
      {{ form_field.errors }}
    </div>
    """
    return _render_field(TEXT_INPUT_TEMPLATE, form_field, **attrs)


@register.simple_tag
def render_select_input(form_field, **attrs):
    SELECT_INPUT_TEMPLATE = """
    <div class="form-control w-full" {% include "generic/attrs.html" with attrs=control_attrs %}>
      <label class="label font-bold" for="{{ form_field.id_for_label }}">{{ form_field.label }}</label>
      {{ form_field }}
      <small class="form-text text-muted">{{ form_field.help_text|safe }}</small>
      {{ form_field.errors }}
    </div>
    """
    return _render_field(SELECT_INPUT_TEMPLATE, form_field, **attrs)


@register.simple_tag
def render_checkbox_input(form_field, **attrs):
    CHECKBOX_INPUT_TEMPLATE = """
    <div class="form-control" {% include "generic/attrs.html" with attrs=control_attrs %}>
      <div class="form-check">
        <label class="label font-bold cursor-pointer">
          <span class="label-text">{{ form_field.label }}</span> 
          {{ form_field }}
        </label>
      </div>
      <small class="form-text text-muted">{{ form_field.help_text|safe }}</small>
      {{ form_field.errors }}
    </div>
    """
    return _render_field(CHECKBOX_INPUT_TEMPLATE, form_field, **attrs)


def _render_field(template_text, form_field, **attrs):
    control_attrs = form_field.field.widget.attrs.pop("control_attrs", None) or {}
    if not form_field.is_hidden:
        template_object = template.Template(template_text)
    else:
        template_object = template.Template("{{ form_field }}")
    control_attrs = control_attrs | _transform_x_attrs(attrs)
    context = template.Context({"form_field": form_field, "control_attrs": control_attrs})
    return template_object.render(context)


def _transform_x_attrs(attrs):
    """
    This converts attributes like `xbind__placeholder` to `x-bind:placeholder`.

    No support for `@click` style attributes or `.` modifiers
    """

    def _make_x_attr(key):
        if key.startswith("x"):
            # support `x-bind:placeholder` style options
            key = key[1:].replace("__", ":")
            return f"x-{key}"
        return key

    return {_make_x_attr(key): value for key, value in attrs.items()}
