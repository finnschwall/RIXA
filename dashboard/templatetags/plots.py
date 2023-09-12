from django import template
import django.utils.html as util
import plotly
from plotly.offline import plot
import django.utils.safestring as safestring

register = template.Library()


@register.simple_tag()
def plotly():
    return util.format_html('<script src="https://cdn.plot.ly/plotly-2.20.0.min.js" charset="utf-8"></script>')


@register.simple_tag()
def draw_plot(fig):
    plot_div = plot([fig], output_type='div', include_plotlyjs=False)
    return safestring.mark_safe(plot_div)


@register.simple_tag(takes_context=True)
def test_plot(context, format_string):
    print(context)
    print(format_string)
    return ""
