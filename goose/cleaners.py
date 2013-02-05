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


class DocumentCleaner(object):

    def __init__(self):

        self.regExRemoveNodes = (
        "^side$|combx|retweet|fontresize|mediaarticlerelated|menucontainer|navbar"
        "|comment|PopularQuestions|foot|footer|Footer|footnote"
        "|cnn_strycaptiontxt|links|meta$|scroll|shoutbox|sponsor"
        "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
        "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
        "|welcome_form|contentTools2|the_answers"
        "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings"
        "|date|^print$|popup|author-dropdown|tools|socialtools|byline"
        "|konafilter|KonaFilter|breadcrumbs|^fn$|wp-caption-text"
        "|source|legende|ajoutVideo|timestamp"
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

    def clean(self, article):

        docToClean = article.doc
        docToClean = self.removeListsWithLinks(docToClean)
        docToClean = self.cleanBadTags(docToClean)
        docToClean = self.dropTags(docToClean,['em','strong'])
        docToClean = self.removeDropCaps(docToClean)
        docToClean = self.removeScriptsAndStyles(docToClean)
        docToClean = self.removeNodesViaRegEx(docToClean, self.captionPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.googlePattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.entriesPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.facebookPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.facebookBroadcastingPattern)
        docToClean = self.removeNodesViaRegEx(docToClean, self.twitterPattern)
        docToClean = self.cleanUpSpanTagsInParagraphs(docToClean)
        docToClean = self.convertDivsToParagraphs(docToClean, 'div')
        docToClean = self.convertDivsToParagraphs(docToClean, 'span')
        return docToClean

    def removeListsWithLinks(self, doc):
        for tag in ['ol','ul']:
            items=Parser.getElementsByTag(doc, tag=tag)
            for item in items:
		fa = 0
                for li in item:
                    if Parser.getElementsByTag(li, tag='a'):
                        fa += 1
                        if fa > 2:
                            Parser.remove(item)
                            break
                    else:
                       fa = 0
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

    def removeScriptsAndStyles(self, doc):
        # remove scripts
        scripts = Parser.getElementsByTag(doc, tag='script')
        for item in scripts:
            Parser.remove(item)

        # remove noscripts
        noscripts = Parser.getElementsByTag(doc, tag='noscript')
        for item in noscripts:
            Parser.remove(item)

        # remove styles
        styles = Parser.getElementsByTag(doc, tag='style')
        for item in styles:
            Parser.remove(item)

        # remove comments
        comments = Parser.getComments(doc)
        for item in comments:
            Parser.remove(item)

        return doc

    def cleanBadTags(self, doc):

        # ids
        naughtyList = doc.xpath(self.queryNaughtyIDs,
                                        namespaces={'re': self.regexpNS})
        naughtyList1 = doc.xpath(self.queryNaughtyIDs1,
                                        namespaces={'re': self.regexpNS})
        for node in naughtyList:
            if node not in naughtyList1: Parser.remove(node)

        # class
        naughtyClasses = doc.xpath(self.queryNaughtyClasses,
                                        namespaces={'re': self.regexpNS})
        naughtyClasses1 = doc.xpath(self.queryNaughtyClasses1,
                                        namespaces={'re': self.regexpNS})
        for node in naughtyClasses:
            if node not in naughtyClasses1: Parser.remove(node)

        # name
        naughtyNames = doc.xpath(self.queryNaughtyNames,
                                        namespaces={'re': self.regexpNS})
        naughtyNames1 = doc.xpath(self.queryNaughtyNames1,
                                        namespaces={'re': self.regexpNS})
        for node in naughtyNames:
            if node not in naughtyNames1: Parser.remove(node)

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
                div.clear()

                for c, n in enumerate(replaceNodes):
                    div.insert(c, n)

                elseDivs += 1

        return doc


class StandardDocumentCleaner(DocumentCleaner):
    pass
