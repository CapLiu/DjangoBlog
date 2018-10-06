from django import template
register = template.Library()

@register.filter(name='script')
def script(value):
    temp = value.replace('<script>','&lt;script&gt;')
    return '<pre>' + temp.replace('</script>','&lt;/script&gt;') + '</pre>'