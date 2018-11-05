import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'myblog.settings'
import django
django.setup()

from blogs.models import Blog
import django.db.models.fields
from django.db.models import *
#from django.contrib.auth.models import User
import whoosh.fields
from whoosh.fields import *
from whoosh.index import create_in,exists,exists_in
from whoosh.filedb.filestore import FileStorage
from ckeditor_uploader.fields import RichTextUploadingField
from whoosh.writing import AsyncWriter
from whoosh.qparser import QueryParser
import whoosh.highlight as highlight

from django.utils.html import strip_tags
from whoosh.qparser import MultifieldParser
class BlogFormatter(highlight.Formatter):
    def format_token(self, text, token, replace=False):
        tokentext = highlight.get_text(text,token,replace)
        return '<b>%s</b>' % strip_tags(tokentext)



# print(User._meta.get_fields())

class searchengine:

    def __init__(self, model, updatefield, indexpath = None, indexname = None):
        self.model = model
        self.indexpath = indexpath
        self.indexname = indexname
        self.updatefield = updatefield
        self.indexschema = {}
        # 建立index存放路径
        if self.indexpath is None:
            self.indexpath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'engineindex/')
        if self.indexname is None:
            self.indexname = model.__name__
        self.__buildSchema()
        self.__buildindex()
        
    # 为某个model建立schema
    def __buildSchema(self):
        self.indexschema = {}
        modlefields = self.model._meta.get_fields()
        for field in modlefields:
            if type(field) == CharField:
                self.indexschema[field.__str__().split('.')[-1]] = TEXT(stored=True)
            elif type(field) == IntegerField:
                self.indexschema[field.__str__().split('.')[-1]] = NUMERIC(stored=True,numtype=int)
            elif type(field) == FloatField:
                self.indexschema[field.__str__().split('.')[-1]] = NUMERIC(stored=True,numtype=float)
            elif type(field) == DateField or type(field) == DateTimeField:
                self.indexschema[field.__str__().split('.')[-1]] = DATETIME(stored=True)
            elif type(field) == BooleanField:
                self.indexschema[field.__str__().split('.')[-1]] = BOOLEAN(stored=True)
            elif type(field) == AutoField:
                self.indexschema[field.__str__().split('.')[-1]] = STORED()
            elif type(field) == RichTextUploadingField:
                self.indexschema[field.__str__().split('.')[-1]] = TEXT(stored=True)


    def __buildindex(self):
        #schemadict = self.__buildSchema()
        document_dic = {}
        # defaultFolderPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'engineindex/')
        if self.indexschema is None:
            return False

        if not os.path.exists(self.indexpath):
            os.mkdir(self.indexpath)

        modelSchema = Schema(**self.indexschema)
        storage = FileStorage(self.indexpath)
        if not exists_in(self.indexpath,indexname=self.indexname):
            ix = create_in(self.indexpath,modelSchema,indexname=self.indexname)
            print('index is created')
            writer = ix.writer()
            # 将model对象依次加入index中
            objectlist = self.model.objects.all()
            for obj in objectlist:
                for key in self.indexschema:
                    if hasattr(obj,key):
                        # print(key,getattr(obj,key.split('.')[-1]))
                        document_dic[key] = getattr(obj,key)
                writer.add_document(**document_dic)
                document_dic.clear()
            writer.commit()
            print('all blog has indexed')
            storage.close()

    def __addonedoc(self,writer,docId):
        print('docId is %s' % docId)
        obj = self.model.objects.get(id=docId)
        document_dic = {}
        print('enter __addonedoc')
        for key in self.indexschema:
            print('key in __addonedoc is %s' % key)
            print(key.split('.')[-1])
            if hasattr(obj,key.split('.')[-1]):
                document_dic[key] = getattr(obj,key.split('.')[-1])
        print(document_dic)
        writer.add_document(**document_dic)



    def updateindex(self):
        print('updateindex')
        storage = FileStorage(self.indexpath)
        ix = storage.open_index(indexname=self.indexname)
        index_id = set()
        to_index_id = set()
        objlist = self.model.objects.all()
        with ix.searcher() as searcher:
            writer = AsyncWriter(ix)
            for indexfield in searcher.all_stored_fields():
                #print(indexfield)
                if len(indexfield) > 0:
                    indexId = indexfield['id']
                    print(indexId)
                    index_id.add(indexId)
                    #print(index_id)
                    #print(to_index_id)
                    # 数据库未找到此篇，则可能已被删除，故从index中删除此篇
                    if not self.model.objects.filter(id=indexId):
                        print(indexId)
                        writer.delete_by_term('id', indexId.__str__())
                        print('delete id is %s' % indexId)

                    for key in indexfield:
                        # 根据updatefield进行更新
                        print(key)
                        if key == self.updatefield:
                            objfromdb = self.model.objects.get(id=indexId)
                            contentofobj = getattr(objfromdb,self.updatefield)
                            if contentofobj != indexfield[key]:
                                writer.delete_by_term('id',indexId.__str__())
                                to_index_id.add(indexId)
                                print('update id is %s, title is %s' % (indexId,objfromdb.title))
            print(index_id)
            print(to_index_id)
            for obj in objlist:
                if obj.id in to_index_id or obj.id not in index_id:
                    self.__addonedoc(writer,obj.id)
                    print('add id is %s, title is %s' % (obj.id,obj.title))
            writer.commit()
        storage.close()

    def __handleUpdate(self, sender, instance, **kwargs):
        self.updateindex()

    def search(self,searchfield,searchkeyword):
        storage = FileStorage(self.indexpath)
        ix = storage.open_index(indexname=self.indexname)
        if isinstance(searchfield,str):
            qp = QueryParser(searchfield,schema=self.indexschema)
        elif isinstance(searchfield,list):
            qp = MultifieldParser(searchfield,schema=self.indexschema)
        q = qp.parse(searchkeyword)
        resultobjlist = []
        hi = highlight.Highlighter()
        with ix.searcher() as searcher:
            results = searcher.search(q,limit=None)
            results.formatter = BlogFormatter()
            for result in results:
                obj_dict = {}
                highlightresults = []
                for key in result:
                    obj_dict[key] = result[key]
                if isinstance(searchfield,str):
                    highlightresults.append({searchfield:'<'+result.highlights(searchfield) + '>'})
                elif isinstance(searchfield,list):
                    for _field in searchfield:
                        highlightresults.append({_field:'<' + result.highlights(_field) + '>'})
                obj_dict['highlight'] = highlightresults
                print(obj_dict['highlight'])
                extradata = extradata()
                if len(extradata) > 0:
                    obj_dict.update(**extradata)
                resultobjlist.append(obj_dict)
        storage.close()
        return resultobjlist

    def extradata(self):
        # 提供用户自定义数据
        return {}




if __name__ == '__main__':
    myengine = searchengine(Blog,'content',indexname='myblogindex')
    #resultlist = myengine.search(['title','content'],'test')
    resultlist = myengine.search('content', 'test')
    #print(resultlist)
