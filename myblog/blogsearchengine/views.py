from django.shortcuts import render
from django.views import View
from blogsearchengine.searchForm import enginebasesearchForm
from blogsearchengine.engine import searchengine
# Create your views here.


class baseSearchView(View):
    form_class = enginebasesearchForm
    modelname = None
    searchfield = None
    updatefield = None
    templatename=''
    indexname=''
    def get(self,request):
        form = self.form_class()
        keycode = request.GET['searchKeyword']
        engine = searchengine(self.modelname, self.updatefield, indexname=self.indexname)
        searchresult = engine.search(self.searchfield, keycode)
        content = {
            'searchResult': searchresult,
            'searchform': form,
        }
        extradata = self.extradata()
        content.update(extradata)
        return render(request, self.templatename, content)

    def extradata(self):
        return {}

