# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from goose.parsers import Parser
from goose.utils import ReplaceSequence
from HTMLParser import HTMLParser
import lxml.html
import re


class DocumentCleaner(object):

    def __init__(self):

        self.regExRemoveNodes = (
        "^side$|combx|retweet|fontresize|mediaarticlerelated|menucontainer|navbar"
        "|comment|PopularQuestions|foot|footer|Footer|footnote"
        "|cnn_strycaptiontxt|links|meta$|scroll|shoutbox|sponsor"
        "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
        "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
        "|welcome_form|contentTools2|the_answers|rating"
        "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings|articlead|articleImage|slideshowInlineLarge|article-side-rail"
        "|date|^print$|popup|author-dropdown|tools|socialtools"
        "|konafilter|KonaFilter|breadcrumbs|^fn$|wp-caption-text"
        "|source|legende|ajoutVideo|timestamp|menu|error"
        )
        self.regExNotRemoveNodes = ("and|no|article|body|column|main|shadow")
        self.regexpNS = "http://exslt.org/regular-expressions"
        self.divToPElementsPattern = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)"
        self.captionPattern = "^caption$"
#        self.googlePattern = " google "
#        self.entriesPattern = "^[^entry-]more.*$"
#        self.facebookPattern = "[^-]facebook"
#        self.facebookBroadcastingPattern = "facebook-broadcasting"
#        self.twitterPattern = "[^-]twitter"
        self.tabsAndNewLinesReplcesments = ReplaceSequence()\
                                            .create("\n", "\n\n")\
                                            .append("\t")\
                                            .append("^\\s+$")
        self.todel = self.regExRemoveNodes.lower().split('|')
        self.notdel = self.regExNotRemoveNodes.lower().split('|')
        

    def clean(self, article):

        docToClean = article.doc
        nodelist = self.getNodesToDelete(docToClean)
        for node in nodelist: Parser.remove(node)  
        docToClean = self.removeListsWithLinks(docToClean)
        docToClean = self.removeDropCaps(docToClean)
        docToClean = self.removeNodesViaRegEx(docToClean, self.captionPattern)
#        docToClean = self.removeNodesViaRegEx(docToClean, self.googlePattern)
#        docToClean = self.removeNodesViaRegEx(docToClean, self.entriesPattern)
#        docToClean = self.removeNodesViaRegEx(docToClean, self.facebookPattern)
#        docToClean = self.removeNodesViaRegEx(docToClean, self.facebookBroadcastingPattern)
#        docToClean = self.removeNodesViaRegEx(docToClean, self.twitterPattern)
        docToClean = self.cleanUpSpanTagsInParagraphs(docToClean)
        docToClean = self.convertDivsToParagraphs(docToClean, 'div')
        return docToClean

    def getNodesToDelete(self, doc):
        nodelist = []
        for node in doc:
            if node.tag in ['script','noscript','style','option','iframe','noframe'] or isinstance(node,lxml.html.HtmlComment) or str(node.tag)[0] == '<':
                nodelist.append(node)
                continue
            if node.tag == 'span' and len(node) == 0 and (node.text == None or len(node.text) < 30):
                node.drop_tag()
                continue
            if node.tag in ['p','span','b','h1','h2','h3','h4','h5'] and len(node) == 0: continue; # good top level nodes
            if node.tag == 'div' and node.getparent().tag == 'span': node.getparent().tag = 'div' # convert span to div
            if node.tag == 'br': # retain line breaks
                if node.tail is not None: node.tail = u'\ufffc ' + node.tail
                else: node.tail = u'\ufffc'
                nodelist.append(node)
                continue
            ids = ''
            if node.attrib.has_key('class'): ids += ' ' + node.attrib['class'].lower() + ' '
            if node.attrib.has_key('id'):    ids += ' ' + node.attrib['id'].lower() + ' '
            if node.attrib.has_key('name'):  ids += ' ' + node.attrib['name'].lower() + ' '
            good_word = ''
            for word in self.notdel:
                if ids.find(word) >= 0: 
                    good_word = word
                    continue
            bad_word = ''
            for word in self.todel:
                if ids.find(word) >= 0: 
                    bad_word = word
                    break
            if (bad_word != '' and good_word == '') or (bad_word != '' and bad_word.find(good_word) >= 0):
                nodelist.append(node)
                continue 
            if 'mod-washingtonpostarticletext' in ids: # washingtonpost hack
                self.aggregateBlocks(doc, '.mod-washingtonpostarticletext')
            nodelist += self.getNodesToDelete(node)
        return nodelist

    def aggregateBlocks(self, doc, selector):
        divs = doc.cssselect(selector)
        if len(divs) <= 1: return
        for i in range(1,len(divs)):
            divs[0].append(divs[i])
            divs[i].tail = None
            divs[i].attrib['class'] = '' # drop all attributes

    def removeWrapedLinks(self, e):
        if e is None or len(e) != 1 or e[0].tag != 'a': return []
        text = ''
        if e.text is not None: text += e.text
        if e[0].tail is not None: text += e[0].tail
        if e.tail is not None: text += e.tail
        if re.search('[^ \t\r\n]',text): return []
        toRemove = [e] + self.removeWrapedLinks(Parser.nextSibling(e))
        return toRemove

    def removeListsWithLinks(self, doc):
        for tag in ['ol','ul']:
            items=Parser.getElementsByTag(doc, tag=tag)
            for item in items:
                fa = 0
                for li in item:
                    if Parser.getElementsByTag(li, tag='a'):
                        fa += 1
                        if fa > 2:
                            parent = item.getparent()
                            Parser.remove(item)
                            if parent is not None:
                                if len(parent) == 0 or len(Parser.getText(parent).split()) < 4:
                                    Parser.remove(parent)
                            break
                    else:
                       fa = 0

        items=Parser.getElementsByTag(doc, tag='a')
        for a in items:
                e = a.getparent()
		if e is None: continue
	        text = Parser.getText(e)
		ldels = []
                textcount = 0
		for link in e:
	            ltext = Parser.getText(link)
                    if link.tag != 'a' and len(ltext) <= 2: continue
		    if link.tag != 'a' and len(ltext) > 2:
                        ldels = []
                        break
                    if ltext == '': continue
	            ldel = text.split(ltext,1)
	            ld = ldel[0].strip()
	            ldels.append(ld)
                    if len(ldel) == 1: break
	            text = ldel[1]
	        if len(ldels) == 0 or ldels[0] == ',': continue
	        else:
                    del ldels[0]
                    flag = 0; flag1 = 0; flag2 = 0; flag3 = 0
	            for ldel in ldels:
			if ldel == ldels[0]: flag += 1
                        if len(ldel) > 3 or ldel.find(',') >= 0: flag1 = 1
			if ldel != '': flag2 = 1
                        if len(ldel) > 1: flag3 = 1
                    if flag2 == 0 and len(ldels) > 1: 
			Parser.remove(e)
			continue
                    if  len(ldels) == 2 and ldels[0] == '|' and ldels[1] == '|': 
			Parser.remove(e)
			continue
                    if  len(ldels) > 3 and flag3 == 0: 
			Parser.remove(e)
			continue
                    if (flag <= 2 and len(ldels) <= 2) or flag1 != 0: 
			continue
		         
	        Parser.remove(e)

        return doc

        items=Parser.getElementsByTag(doc, tag='a')
        for a in items:
                e = a.getparent()
                if e is None: continue
                if len(e) == 1: 
                    toRemove = self.removeWrapedLinks(e)
                    if len(toRemove) > 5:
                        for bn in toRemove:
                            Parser.remove(bn)

        return doc

    def dropTags(self, doc, tags):
        for tag in tags:
            ems = Parser.getElementsByTag(doc, tag=tag)
            for node in ems:
                images = Parser.getElementsByTag(node, tag='img')
                if len(images) == 0:
                    node.drop_tag()
        return doc

    def removeDropCaps(self, doc):
        items = doc.cssselect("span[class~=dropcap], span[class~=drop_cap]")
        for item in items:
            item.drop_tag()

        return doc

    def removeNodesViaRegEx(self, doc, pattern):
        for selector in ['id', 'class']:
            reg = "//*[re:test(@%s, '%s', 'i')]" % (selector, pattern)
            naughtyList = doc.xpath(reg, namespaces={'re': self.regexpNS})
            for node in naughtyList:
                Parser.remove(node)
        return doc

    def cleanUpSpanTagsInParagraphs(self, doc):
        spans = doc.cssselect('p > span')
        for item in spans:
            item.drop_tag()
        return doc


    def getFlushedBuffer(self, replacementText, doc):
        return Parser.textToPara('<p>' + replacementText + '</p>')

    def getReplacementNodes(self, doc, div):
        goodInlineTags = ['b','strong','em','i','a','img','big','cite','code','q','s','small','strike','sub','tt','u','var']

        replacementText = []
        nodesToReturn = []
        nodesToRemove = []
        childs = Parser.childNodesWithText(div)
        for kid in childs:
            if Parser.isTextNode(kid):
                if kid.text != None: replaceText = HTMLParser().unescape(kid.text).strip('\t\r\n')
		else: replaceText = ''
                if(len(replaceText)) > 0: replacementText.append(replaceText)
            elif Parser.getTag(kid) in goodInlineTags:
                outer = Parser.outerHtml(kid)
                replacementText.append(outer)
                nodesToRemove.append(kid)
            else:
                if(len(replacementText) > 0):
                    newNode = self.getFlushedBuffer(''.join(replacementText), doc)
                    nodesToReturn.append(newNode)
                    replacementText = []
                nodesToReturn.append(kid)

        # flush out anything still remaining
        if(len(replacementText) > 0):
            newNode = self.getFlushedBuffer(''.join(replacementText), doc)
            nodesToReturn.append(newNode)
            replacementText = []

        for n in nodesToRemove:
            Parser.remove(n)

        return nodesToReturn

    def replaceElementsWithPara(self, doc, div):
        Parser.replaceTag(div, 'p')

    def convertDivsToParagraphs(self, doc, domType):
        badDivs = 0
        elseDivs = 0
        divs = Parser.getElementsByTag(doc, tag=domType)
        tags = ['a', 'blockquote', 'dl', 'div', 'img', 'ol', 'p', 'pre', 'table', 'ul']

        for div in divs:
            items = Parser.getElementsByTags(div, tags)
            if div is not None and len(items) == 0:
                self.replaceElementsWithPara(doc, div)
                badDivs += 1
            elif div is not None:
                replaceNodes = self.getReplacementNodes(doc, div)
                text = div.tail
                div.clear()

                for c, n in enumerate(replaceNodes):
                    div.insert(c, n)
                div.tail = text
                elseDivs += 1

        return doc


class StandardDocumentCleaner(DocumentCleaner):
    pass
