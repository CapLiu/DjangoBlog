from django import template
from django.template import Context
from django.utils.html import strip_tags
register = template.Library()

@register.tag
def highlightresult(parser,token):
    # syntax
    # {% highlightresult result font "<b>" %}
    # {% highlightresult result css "classname" %}
    try:
        format_string_list = token.split_contents()
        tag_name = format_string_list[0]
        highlightcontent = format_string_list[1]
        format_string = format_string_list[2]+' '+format_string_list[3]
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % tag_name)
    return SearchResultNode(highlightcontent,format_string)

class SearchResultNode(template.Node):
    def __init__(self,highlightcontent,format_string):
        self.format_string = format_string
        self.highlight_content = template.Variable(highlightcontent)

    def render(self, context):
        actual_content = self.highlight_content.resolve(context)
        actual_content = actual_content.replace('<script>','&lt;script&gt;').replace('</script>','&lt;/script&gt;')
        style_tag = self.format_string.split(' ')[0]
        if style_tag == 'font':
            style_tag_element = self.format_string.split(' ')[1][2:-2]
            style_tag = '<%s>' % style_tag_element
            anti_style_tag = '</%s>' % style_tag_element
        elif style_tag == 'css':
            style_tag_element = self.format_string.split(' ')[1]
            style_tag = '<span class=%s>' % style_tag_element
            anti_style_tag = '</span>'
        #return '<b>' + actual_content + '</b>'
        return style_tag+actual_content+anti_style_tag
