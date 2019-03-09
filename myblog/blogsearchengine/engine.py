import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'myblog.settings'
import django
django.setup()


from blogs.models import Blog
from django.db.models import *

from whoosh.fields import *
from whoosh.index import create_in,exists,exists_in
from whoosh.filedb.filestore import FileStorage
from ckeditor_uploader.fields import RichTextUploadingField
from whoosh.writing import AsyncWriter

import whoosh.highlight as highlight
from whoosh.qparser import QueryParser
from django.utils.html import strip_tags
from whoosh.qparser import MultifieldParser
from whoosh.qparser import OrGroup



class BlogFormatter(highlight.Formatter):
    def format_token(self, text, token, replace=False):
        tokentext = highlight.get_text(text,token,replace)
        return '<b>%s</b>' % strip_tags(tokentext)



# print(User._meta.get_fields())

class searchengine:

    def __init__(self, model, updatefield, indexpath = None, indexname = None,formatter = None,advancemode=True):
        self.model = model
        self.indexpath = indexpath
        self.indexname = indexname
        self.updatefield = updatefield
        self.indexschema = {}
        self.formatter = BlogFormatter
        self.advancemode = advancemode
        # 建立index存放路径
        if self.indexpath is None:
            self.indexpath = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'engineindex/')
        if self.indexname is None:
            self.indexname = model.__name__
        if formatter is not None:
            self.formatter = formatter
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
            elif type(field) == ForeignKey and self.advancemode == True:
                subschema = self.__buildModelSchema(field.related_model)
                self.indexschema.update(**subschema)
        #print(self.indexschema)

    def __buildModelSchema(self,dedicatedmodel):
        modelschema = {}
        modelfields = dedicatedmodel._meta.get_fields()
        for field in modelfields:
            if type(field) == CharField:
                modelschema[dedicatedmodel.__name__ + '_' + field.__str__().split('.')[-1]] = TEXT(stored=True)
            elif type(field) == IntegerField:
                modelschema[dedicatedmodel.__name__ + '_' + field.__str__().split('.')[-1]] = NUMERIC(stored=True,numtype=int)
            elif type(field) == FloatField:
                modelschema[dedicatedmodel.__name__ + '_' + field.__str__().split('.')[-1]] = NUMERIC(stored=True,numtype=float)
            elif type(field) == DateField or type(field) == DateTimeField:
                modelschema[dedicatedmodel.__name__ + '_' + field.__str__().split('.')[-1]] = DATETIME(stored=True)
            elif type(field) == BooleanField:
                modelschema[dedicatedmodel.__name__ + '_' + field.__str__().split('.')[-1]] = BOOLEAN(stored=True)
            elif type(field) == AutoField:
                modelschema[dedicatedmodel.__name__ + '_' + field.__str__().split('.')[-1]] = STORED()
            elif type(field) == RichTextUploadingField:
                modelschema[dedicatedmodel.__name__ + '_' + field.__str__().split('.')[-1]] = TEXT(stored=True)
            elif type(field) == ForeignKey:
                subschema = self.__buildModelSchema(field.related_model)
                modelschema.update(**subschema)
        return modelschema



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
                    else:
                        if self.advancemode:
                            # 该key属于外键
                            foreignmodel = key.split('_')[0]
                            foreignkey = key[key.find('_')+1:]
                            for field in self.model._meta.get_fields():
                                if type(field) == ForeignKey:
                                    if field.related_model.__name__ == foreignmodel:
                                        print(field.__str__().split('.')[-1])
                                        foreignobj = getattr(obj,field.__str__().split('.')[-1])
                                        if hasattr(foreignobj,foreignkey):
                                            print(key)
                                            document_dic[key] = getattr(foreignobj,foreignkey)


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
            print(key)
            if hasattr(obj,key):
                document_dic[key] = getattr(obj,key)
            else:
                if self.advancemode:
                    # 该key属于外键
                    foreignmodel = key.split('_')[0]
                    foreignkey = key[key.find('_') + 1:]
                    for field in self.model._meta.get_fields():
                        if type(field) == ForeignKey:
                            if field.related_model.__name__ == foreignmodel:
                                print(field.__str__().split('.')[-1])
                                foreignobj = getattr(obj, field.__str__().split('.')[-1])
                                if hasattr(foreignobj, foreignkey):
                                    print(key)
                                    document_dic[key] = getattr(foreignobj, foreignkey)
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
                if len(indexfield) > 0:
                    indexId = indexfield['id']
                    print(indexId)
                    index_id.add(indexId)
                    # 数据库未找到此篇，则可能已被删除，故从index中删除此篇
                    if not self.model.objects.filter(id=indexId):
                        print(indexId)
                        writer.delete_by_term('id', str(indexId))
                    else:
                        for key in indexfield:
                            # 根据updatefield进行更新
                            if key == self.updatefield:
                                print(indexId)
                                objfromdb = self.model.objects.get(id=indexId)
                                contentofobj = getattr(objfromdb,self.updatefield)
                                if contentofobj != indexfield[key]:
                                    writer.delete_by_term('id',str(indexId))
                                    to_index_id.add(indexId)
                                    print('update id is %s, title is %s' % (indexId,objfromdb.title))
            for obj in objlist:
                if obj.id in to_index_id or obj.id not in index_id:
                    self.__addonedoc(writer,obj.id)
                    print('add id is %s, title is %s' % (obj.id,obj.title))
            writer.commit()
        storage.close()

    def __handleUpdate(self, sender, instance, **kwargs):
        self.updateindex()

    def __get_modelname_fields(self,foreignmodel,sfield):
        fields = foreignmodel._meta.get_fields()
        found = False
        for m_field in fields:
            if m_field.__str__().split('.')[-1] == sfield:
                return foreignmodel.__name__ + '_' + sfield
        for m_field in fields:
            if type(m_field) == ForeignKey:
                return self.__get_modelname_fields(m_field.related_model,m_field)
        if not found:
            return sfield

    def __recreate_field(self,searchfield):
        fields = self.model._meta.get_fields()
        for modelfield in fields:
            if isinstance(searchfield,str):
                if modelfield.__str__().split('.')[-1] == searchfield:
                    print(modelfield.__str__())
                    print('Non-foreign')
                    return searchfield
        print(searchfield)
        for modelfield in fields:
            if isinstance(searchfield,str):
                if type(modelfield) == ForeignKey:
                    print('Foreign')
                    return self.__get_modelname_fields(modelfield.related_model,searchfield)
        return searchfield

    def search(self,searchfield,searchkeyword,ignoretypo = False):
        storage = FileStorage(self.indexpath)
        ix = storage.open_index(indexname=self.indexname)
        if self.advancemode:
            if isinstance(searchfield,str):
                searchfield = self.__recreate_field(searchfield)
            elif isinstance(searchfield,list):
                newsearchfields = []
                for s_field in searchfield:
                    newsearchfields.append(self.__recreate_field(s_field))
                searchfield = newsearchfields
            print(searchfield)
        if isinstance(searchfield,str):
            qp = QueryParser(searchfield, schema=self.indexschema, group=OrGroup)
        elif isinstance(searchfield,list):
            qp = MultifieldParser(searchfield, schema=self.indexschema)
        q = qp.parse(searchkeyword)
        resultobjlist = []
        corrected_dict = {}
        with ix.searcher() as searcher:
            corrected = searcher.correct_query(q,searchkeyword)
            if corrected.query != q and ignoretypo == False:
                q = qp.parse(corrected.string)
                corrected_dict = {'corrected': u'您要找的是不是' + corrected.string}
            results = searcher.search(q,limit=None)
            #results.formatter = BlogFormatter()
            results.formatter = self.formatter()
            print(results)
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
                extradata_dic = self.extradata()
                if len(extradata_dic) > 0:
                    obj_dict.update(**extradata_dic)
                resultobjlist.append(obj_dict)
        storage.close()
        return resultobjlist,corrected_dict

    def extradata(self):
        # 提供用户自定义数据
        return {}




if __name__ == '__main__':
    myengine = searchengine(Blog,'content',indexname='myblogindex')
    #resultlist = myengine.search(['title','content'],'test')
    #resultlist = myengine.search(['con','username'], 'test')
    myengine.updateindex()
    #print(resultlist)
