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
import lxml.html


class DocumentCleaner(object):

    def __init__(self):

        self.regExRemoveNodes = (
        "^side$|combx|retweet|fontresize|mediaarticlerelated|menucontainer|navbar"
        "|comment|PopularQuestions|foot|footer|Footer|footnote"
        "|cnn_strycaptiontxt|links|meta$|scroll|shoutbox|sponsor"
        "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
        "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
        "|welcome_form|contentTools2|the_answers|rating"
        "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings"
        "|date|^print$|popup|author-dropdown|tools|socialtools|byline"
        "|konafilter|KonaFilter|breadcrumbs|^fn$|wp-caption-text"
        "|source|legende|ajoutVideo|timestamp|menu"
        )
        self.regExNotRemoveNodes = ("and|no|article|body|column|main|shadow")
        self.regexpNS = "http://exslt.org/regular-expressions"
        self.queryNaughtyIDs = "//*[re:test(@id, '%s', 'i')]" % self.regExRemoveNodes
        self.queryNaughtyClasses = "//*[re:test(@class, '%s', 'i')]" % self.regExRemoveNodes
        self.queryNaughtyNames = "//*[re:test(@name, '%s', 'i')]" % self.regExRemoveNodes
        self.queryNaughtyIDs1 = "//*[re:test(@id, '%s', 'i')]" % self.regExNotRemoveNodes
        self.queryNaughtyClasses1 = "//*[re:test(@class, '%s', 'i')]" % self.regExNotRemoveNodes
        self.queryNaughtyNames1 = "//*[re:test(@name, '%s', 'i')]" % self.regExNotRemoveNodes
        self.divToPElementsPattern = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)"
        self.captionPattern = "^caption$"
        self.googlePattern = " google "
        self.entriesPattern = "^[^entry-]more.*$"
        self.facebookPattern = "[^-]facebook"
        self.facebookBroadcastingPattern = "facebook-broadcasting"
        self.twitterPattern = "[^-]twitter"
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
        docToClean = self.dropTags(docToClean,['em','strong'])
        docToClean = self.removeDropCaps(docToClean)
        docToClean = self.removeNodesViaRegEx(docToClean, self.captionPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.googlePattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.entriesPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.facebookPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.facebookBroadcastingPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.twitterPattern)
        docToClean = self.cleanUpSpanTagsInParagraphs(docToClean)
	docToClean = self.keepLineBreaks(docToClean)
        docToClean = self.convertDivsToParagraphs(docToClean, 'div')
        docToClean = self.convertDivsToParagraphs(docToClean, 'span')
        return docToClean

    def getNodesToDelete(self, doc):
        nodelist = []
        for node in doc:
            if node.tag in ['script','noscript','style','option'] or isinstance(node,lxml.html.HtmlComment):
		nodelist.append(node)
		continue
            ids = ''
            if node.attrib.has_key('class'):
               ids += ' ' + node.attrib['class'].lower()
            if node.attrib.has_key('id'):
               ids += ' ' + node.attrib['id'].lower()
            if node.attrib.has_key('name'):
               ids += ' ' + node.attrib['name'].lower()
            good_node = 0
            for word in self.notdel:
		if ids.find(word) >= 0: 
                    good_node = 1
                    continue
            if good_node == 0:
                good_node = 1
                for word in self.todel:
		    if ids.find(word) >= 0: 
                        good_node = 0
                        break
            if good_node == 0:
                nodelist.append(node)
                continue 
            nodelist += self.getNodesToDelete(node)
        return nodelist

    def keepLineBreaks(self, doc):
        items=Parser.getElementsByTag(doc, tag='br')
	for n in items:
	    if n.tail is not None: n.tail = u'\ufffc ' + n.tail
            else: n.tail = u'\ufffc'
            n.drop_tag()

        items=Parser.getElementsByTag(doc, tag='p')
	for n in items:
	    if n.tail is not None: n.tail = u'\ufffc ' + n.tail
            else: 
                n.tail = u'\ufffc'
#                if n.text is None: n.drop_tag()  # drop empty p
	return doc

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
                    if flag <= 2 and (len(ldels) <= 2 or flag1 != 0): 
			continue
		         
	        Parser.remove(e)
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
        return Parser.textToPara(replacementText)

    def getReplacementNodes(self, doc, div):
        replacementText = []
        nodesToReturn = []
        nodesToRemove = []
        childs = Parser.childNodesWithText(div)

        for kid in childs:
            # node is a p
            # and already have some replacement text
            if Parser.getTag(kid) == 'p' and len(replacementText) > 0:
                newNode = self.getFlushedBuffer(''.join(replacementText), doc)
                nodesToReturn.append(newNode)
                replacementText = []
                nodesToReturn.append(kid)
            # node is a text node
            elif Parser.isTextNode(kid):
                kidTextNode = kid
                kidText = Parser.getText(kid)
                replaceText = self.tabsAndNewLinesReplcesments.replaceAll(kidText)
                if(len(replaceText)) > 1:
                    prevSibNode = Parser.previousSibling(kidTextNode)
                    while prevSibNode is not None \
                        and Parser.getTag(prevSibNode) == "a" \
                        and Parser.getAttribute(prevSibNode, 'grv-usedalready') != 'yes':
                        outer = " " + Parser.outerHtml(prevSibNode) + " "
                        replacementText.append(outer)
                        nodesToRemove.append(prevSibNode)
                        Parser.setAttribute(prevSibNode,
                                    attr='grv-usedalready', value='yes')
                        prev = Parser.previousSibling(prevSibNode)
                        prevSibNode = prev if prev is not None else None
                    # append replaceText
                    replacementText.append(replaceText)
                    #
                    nextSibNode = Parser.nextSibling(kidTextNode)
                    while nextSibNode is not None \
                        and Parser.getTag(nextSibNode) == "a" \
                        and Parser.getAttribute(nextSibNode, 'grv-usedalready') != 'yes':
                        outer = " " + Parser.outerHtml(nextSibNode) + " "
                        replacementText.append(outer)
                        nodesToRemove.append(nextSibNode)
                        Parser.setAttribute(nextSibNode,
                                    attr='grv-usedalready', value='yes')
                        next = Parser.nextSibling(nextSibNode)
                        prevSibNode = next if next is not None else None

            # otherwise
            else:
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
