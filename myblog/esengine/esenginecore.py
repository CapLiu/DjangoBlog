# -*- coding=utf-8 -*-
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'myblog.settings'
import django
django.setup()
from blogs.models import Blog
#from elasticsearch5 import Elasticsearch
from elasticsearch import Elasticsearch
from django.db.models import *
from ckeditor_uploader.fields import RichTextUploadingField
import json
from django.utils.html import strip_tags

class esengine:
    def __init__(self,indexname,doctype,model):
        self.es = Elasticsearch()
        self.createIndex(indexname,doctype,model)

    def __parsefieldname(self,fieldname):
        return fieldname.__str__().split('.')[-1]

    def __getforeignvalue(self,dedicatedmodel,obj):
        modelschema = {}
        modelfields = dedicatedmodel._meta.get_fields()
        for field in modelfields:
            if type(field) == CharField:
                modelschema[dedicatedmodel.__name__ + '_' + self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == IntegerField:
                modelschema[dedicatedmodel.__name__ + '_' + self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == FloatField:
                modelschema[dedicatedmodel.__name__ + '_' + self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == DateField or type(field) == DateTimeField:
                modelschema[dedicatedmodel.__name__ + '_' + self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == RichTextUploadingField:
                modelschema[dedicatedmodel.__name__ + '_' + self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == ForeignKey:
                subschema = self.__getforeignvalue(field.related_model)
                modelschema.update(**subschema)
        return modelschema

    def createIndex(self,indexname,doctype,model):
        if not self.es.indices.exists(indexname):
            modelfields = model._meta.get_fields()
            objectlist = model.objects.all()
            docId = 0
            for obj in objectlist:
                singledoc = {}
                for field in modelfields:
                    if type(field) == CharField:
                        singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
                    elif type(field) == RichTextUploadingField:
                        singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
                    elif type(field) == FloatField:
                        singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
                    elif type(field) == IntegerField:
                        singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
                    elif type(field) == DateField or type(field) == DateTimeField:
                        singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
                    elif type(field) == AutoField:
                        singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
                    elif type(field) == ForeignKey:
                        foreignobj = getattr(obj,self.__parsefieldname(field))
                        subvalue = self.__getforeignvalue(field.related_model,foreignobj)
                        singledoc.update(**subvalue)
                print(singledoc)
                docId = docId + 1
                self.es.index(indexname,doctype,singledoc,docId)

    def clearIndex(self,indexname,doctype):
        for i in range(1,self.es.count(indexname,doctype)['count']+1):
            self.es.delete(indexname, doctype, i)

    def __addOneDoc(self,indexname,doctype,model,objId):
        obj = model.objects.get(id=objId)
        modelfields = model._meta.get_fields()
        singledoc = {}
        for field in modelfields:
            if type(field) == CharField:
                singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == RichTextUploadingField:
                singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == FloatField:
                singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == IntegerField:
                singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == DateField or type(field) == DateTimeField:
                singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == AutoField:
                singledoc[self.__parsefieldname(field)] = getattr(obj, self.__parsefieldname(field))
            elif type(field) == ForeignKey:
                foreignobj = getattr(obj, self.__parsefieldname(field))
                subvalue = self.__getforeignvalue(field.related_model, foreignobj)
                singledoc.update(**subvalue)
        print(singledoc)
        docId = self.es.count(indexname,doctype)['count'] + 1
        self.es.index(indexname, doctype, singledoc, docId)

    def __getvalue(self, indexname, doctype, id, fieldname):
        print(self.es.count(indexname,doctype)['count']+1)
        return self.es.get(indexname,doctype,id)['_source'][fieldname]

    def updateIndex(self,indexname, doctype, model, updatefield):
        index_id = set()
        to_index_id = set()
        print(updatefield)
        #print(self.es.count(indexname,doctype))
        indexfield = model._meta.get_fields()
        objlist = model.objects.all()
        for indexDocId in range(1,self.es.count(indexname,doctype)['count']):
            #print(self.es.get(indexname,indexDocId,doctype))
            docId = self.__getvalue(indexname,doctype,indexDocId,'id')
            index_id.add(docId)
            if not model.objects.get(id=docId):
                # 数据库未找到此篇，则可能已被删除，故从index中删除此篇
                print('delete')
                self.es.delete(indexname, doctype, indexDocId)
            else:
                print('update')
                # 根据updatefield的值进行更新
                for field in indexfield:
                    # 根据updatefield进行更新
                    if self.__parsefieldname(field) == updatefield:
                        print(docId)
                        objfromdb = model.objects.get(id=docId)
                        contentofobj = getattr(objfromdb, updatefield)
                        contentofindex = self.__getvalue(indexname,doctype,indexDocId,updatefield)
                        if contentofobj != contentofindex:
                            print('content in index is %s,content in db is %s' % (contentofindex, contentofobj))
                            to_index_id.add(docId)
                            self.es.delete(indexname, doctype, indexDocId)
        for obj in objlist:
            if obj.id not in index_id or obj.id in to_index_id:
                self.__addOneDoc(indexname,doctype,model,obj.id)

    def basicsearch(self,indexname,doctype,searchfield,keyword):
        if type(searchfield) == str:
            querybody = self.__buildSingleQueryBody(searchfield,keyword)
            res = self.es.search(indexname,doctype,body=querybody)
            totalcount,result = self.__parseresult(res,searchfield)
            if totalcount == 0:
                querybody = self.__buildSingleQueryBody(searchfield,keyword,matchmethod='match_phrase_prefix')
                res = self.es.search(indexname,doctype,body=querybody)
                totalcount,result = self.__parseresult(res,searchfield)
            return totalcount,result

    def multifieldsearch(self,indexname,doctype,searchfield,keyword):
        if type(searchfield) == list:
            querybody = self.__buildMultiQueryBody(searchfield, keyword)
            res = self.es.search(indexname, doctype, body=querybody)
            totalcount, result = self.__parseresult(res, searchfield)
            if totalcount == 0:
                # 去重
                tmpresult = []
                result_ids = set()
                for field in searchfield:
                    querybody = self.__buildSingleQueryBody(field, keyword,matchmethod='match_phrase_prefix')
                    res = self.es.search(indexname, doctype, body=querybody)
                    eachcount,eachresult = self.__parseresult(res, field)
                    totalcount += eachcount
                    result += eachresult
                # 去重
                for singleresult in result:
                    result_ids.add(singleresult['id'])

                for resultId in result_ids:
                    for singleresult in result:
                        if singleresult['id'] == resultId:
                            tmpresult.append(singleresult)
                            break
                result = tmpresult
                totalcount = len(result)
        elif type(searchfield) == str:
            totalcount,result = self.basicsearch(indexname,doctype,searchfield,keyword)
        return totalcount, result

    def __buildSingleQueryBody(self,searchfield,keyword,matchmethod='match'):
        # print(kwargs)
        querystr = ''
        if type(searchfield) == str:
            querystr = '{"query":' \
                       '{"%s":{"%s":"%s"}' \
                       '}' \
                       '}' % (matchmethod,searchfield,keyword)
        body = json.loads(querystr)
        return body

    def advancesearch(self,indexname,doctype,includefields,includekeywords,excludefields,excludekeywords,datefield,startdate,enddate):
        querybody = self.__buildAdvanceQueryBody(includefields,
                                                 includekeywords,
                                                 excludefields,
                                                 excludekeywords,
                                                 datefield,
                                                 startdate,
                                                 enddate)
        print(querybody)
        res = self.es.search(indexname, doctype, body=querybody)
        print(res)
        totalcount, result = self.__parseresult(res, includefields)
        print(result)
        return totalcount,result

    def createSuggester(self,suggestername,searchfield,keyword):
        suggesterstr = '"%s" : {' \
                       '"text" : "%s",' \
                       '"term" : {' \
                       '"field" : "%s"' \
                       '}' \
                       '}' % (suggestername,keyword,searchfield)
        return suggesterstr

    def test(self):
        self.advancesearch('blog','blog_content',['title'],'test',['title'],'0','createdate','2018-01-27','2019-03-01')

    def __buildMultiQueryBody(self,searchfield,keyword):
        if type(searchfield) == list:
            fieldlist = []
            for singlefield in searchfield:
                singlefield = '"' + singlefield + '"'
                fieldlist.append(singlefield)
            fieldstr = ','.join(fieldlist)
            fieldstr = '['+fieldstr +']'
            querystr = '{"query":' \
                       '{"multi_match":' \
                       '{"query": "%s",' \
                       '"fields":%s}' \
                       '}' \
                       '}' % (keyword,fieldstr)
            body = json.loads(querystr)
            return body

    def __buildAdvanceQueryBody(self,includefields,includekeywords,excludefields,excludekeywords,datefield,startdate,enddate):
        querystr = '{"query":{' \
                   '"bool":{'
        must_clause_header = '"must":[ %s ]'
        must_not_clause_header = '"must_not":[ %s ]'
        match_clause = '{ "match": { "%s":"%s" } }'
        range_clause = '{ "range": { "%s" :{ "gte":"%s","lte":"%s" } } }'
        includekeywordlist = includekeywords.split(',')
        excludekeywordlist = excludekeywords.split(',')
        total_include_match = ''
        total_exclude_match = ''
        for includefield in includefields:
            for includekeyword in includekeywordlist:
                if total_include_match != '':
                    total_include_match += ','
                tmp_match_clause = match_clause % (includefield,includekeyword)
                total_include_match += tmp_match_clause

        for excludefield in excludefields:
            for excludekeyword in excludekeywordlist:
                if total_exclude_match != '':
                    total_exclude_match += ','
                tmp_match_clause = match_clause % (excludefield,excludekeyword)
                total_exclude_match += tmp_match_clause

        range_clause_body = range_clause % (datefield, startdate, enddate)
        total_include_match = total_include_match + ',' + range_clause_body
        must_clause_body = must_clause_header % total_include_match
        must_not_clause_body = must_not_clause_header % total_exclude_match
        querystr = querystr + must_clause_body + ',' + must_not_clause_body +'}}}'
        body = json.loads(querystr)
        return body

    def __parseresult(self, res,searchfield):
        parsebody = res['hits']['hits']
        resultcount = res['hits']['total']
        result_list = []
        keyresult = {}
        for hitbody in parsebody:
            keyresult = hitbody['_source']
        # 设置highlight
            if type(searchfield) == str:
                keyresult['highlight'] = keyresult[searchfield]
            elif type(searchfield) == list:
                highlightlist = []
                for _field in searchfield:
                    highlightlist.append(keyresult[_field])
                keyresult['highlight'] = highlightlist
            result_list.append(keyresult)
        return (resultcount,result_list)


if __name__ == '__main__':
    es = esengine('blog','blog_content',Blog)
    #es.createIndex('blog','blog_content',Blog)
    #es.updateIndex('blog','blog_content',Blog,'content')
    #es.basicsearch('blog','blog_content','content','rea')
    #es.buildQueryBody('content','test')
    es.test()
    #es.multifieldsearch('blog', 'blog_content', ['content','title'], 'test')