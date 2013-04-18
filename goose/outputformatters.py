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
from HTMLParser import HTMLParser
from goose.text import innerTrim
from goose.parsers import Parser
import re
import lxml.html

goodBlockTags = ['p','h1','h2','h3','h4','h5']
goodInlineTags = ['b','strong','em','i','a','img','big','cite','code','q','s','small','strike','sub','tt','u','var']
badInlineTags = ['abbr','acronym','basefont','bdo','dfn','font','input','kbd','label','samp','select','span','textarea','sup']

class OutputFormatter(object):

    def __init__(self, config):
        self.topNode = None
        self.config = config
        self.stopwordsCls = config.stopwordsCls

    def getLanguage(self, article):
        """\
        Returns the language is by the article or
        the configuration language
        """
        # we don't want to force the target laguage
        # so we use the article.metaLang
        if self.config.useMetaLanguge == True:
            if article.metaLang:
                return article.metaLang[:2]
        return self.config.targetLanguage

    def getTopNode(self):
        return self.topNode

    def getFormattedText(self, article):
        self.topNode = article.topNode
        self.removeNodesWithNegativeScores()
        self.convertLinksToText()
        self.replaceTagsWithText()
        self.removeParagraphsWithFewWords(article)
        return self.convertToText(article)

    def convertToText(self,article):
        txts = []
        for node in list(self.getTopNode()):
            txt = Parser.getFormattedText(node)
            if txt:
                txt = HTMLParser().unescape(txt)
                txts.append(innerTrim(txt))
        text = '\n'.join(txts)
        text = re.sub(u'[\ufffc]','\n',text)
        lines = text.split('\n')
        text = ''
        # cutting title from article text if found in first 4 rows
        if len(lines) > 4:
            for i in range(0,4):
                if lines[i] == article.h1 or lines[i] == article.title:
                    del lines[i]
                    break
        for line in lines:
            if re.search('[^ \t\r]',line): text += line + '\n'

        return text

    def getFormattedText1(self, article):
        self.topNode = article.topNode

        self.replaceTagsWithText()
        e = lxml.html.HtmlElement(); e.tag = 'div';
        article.topNode.getparent().remove(article.topNode);
        e.append(article.topNode)
        self.convertToText(article.topNode, True)
        for p in article.topNode:
            if p.tag == 'div' or p.tag == 'p':
                p.tag = 'p'
                if (p.text is None or p.text == '') and (p.tail is None or p.tail == ''): Parser.remove(p)
        txt = Parser.nodeToString(e)
        return txt

    def moveAllChilds(self,s,d):
        lst = list(s)
        for el in lst:
            s.remove(el)
            d.append(el)

    def moveNextChilds(self,s):
        p = s.getparent()
        n = s.getnext()
        while n is not None:
            p.remove(n)
            s.append(n)
            n = s.getnext()

    def convertToText1(self, p, mc):
        if p.text is not None: 
            p.text = re.sub('[\t\r\n]','',p.text)
            pars = p.text.split(u'\ufffc')
            if len(pars) > 1:
                p.text = pars[0]
                lst = pars[1:]
                ee = p
                for i in lst:
                    e = lxml.html.HtmlElement(); e.tag = 'div'; e.text = i
                    ee.addnext(e)
                    ee = e
                if e.tail is None: 
                    e.tail = p.tail
                    p.tail = None
                self.moveAllChilds(p,e)
        if p.tail is not None: 
            p.tail = re.sub('[\t\r\n]','',p.tail)
            pars = p.tail.split(u'\ufffc')
            if len(pars) > 1:
                p.tail = pars[0]
                lst = pars[1:]
                ee = p
                for i in lst:
                    e = lxml.html.HtmlElement(); e.tag = 'div'; e.text = i
                    ee.addnext(e)
                    ee = e
                if e.tail is not None: 
                    p.tail = e.tail
                    e.tail = None
                self.moveNextChilds(e)
        if len(p) == 0: return
        n = list(p)[0]
        while n is not None:
            if not mc and n.tag not in goodInlineTags: # block in text block, fix needed
                ni = p.index(n)
                t = p.tail; p.tail = None
                p.remove(n)
                p.addnext(n)
                n.tag = 'div'
                e = lxml.html.HtmlElement(); e.tag = 'div'; e.tail = t
                n.addnext(e)
                if n.tail is not None:
                    t = lxml.html.HtmlElement(); t.tag = 'div'; t.text = n.tail; n.tail = None
                    n.addnext(t)
                lst = list(p)[ni:]
                for el in lst:
                    p.remove(el)
                    e.append(el)
                return
            self.convertToText(n, False)
            if n.tag in goodInlineTags and n.text is None and len(n) == 0:
                np = n; n = n.getnext()
                Parser.remove(np)
            else:
                n = n.getnext()
        return

    def convertLinksToText(self):
        """\
        cleans up and converts any nodes that
        should be considered text into text
        """
        Parser.stripTags(self.getTopNode(), 'a')

    def removeNodesWithNegativeScores(self):
        """\
        if there are elements inside our top node
        that have a negative gravity score,
        let's give em the boot
        """
        return
        gravityItems = self.topNode.cssselect("*[gravityScore]")
        for item in gravityItems:
            score = int(item.attrib.get('gravityScore'), 0)
            if score < 1:
                Parser.remove(item)

    def replaceTagsWithText(self):
        """\
        replace common tags with just
        text so we don't have any crazy formatting issues
        so replace <br>, <i>, <strong>, etc....
        with whatever text is inside them
        code : http://lxml.de/api/lxml.etree-module.html#strip_tags
        """
#        Parser.stripTags(self.getTopNode(), *badInlineTags)
        Parser.stripTags(self.getTopNode(), 'b', 'strong', 'i', 'br', 'sup', 'em')

    def removeParagraphsWithFewWords(self, article):
        """\
        remove paragraphs that have less than x number of words,
        would indicate that it's some sort of link
        """
        return # becouse this wrong logic, links should be removed before this stage, when we can see actual links length
        allNodes = Parser.getElementsByTags(self.getTopNode(), ['*'])  # .cssselect('*')
        allNodes.reverse()
        for el in allNodes:
            text = Parser.getText(el)
            stopWords = self.stopwordsCls(language=self.getLanguage(article)).getStopWordCount(text)
            if stopWords.getStopWordCount() < 3 \
                and len(Parser.getElementsByTag(el, tag='object')) == 0 \
                and len(Parser.getElementsByTag(el, tag='embed')) == 0:
                Parser.remove(el)
            # TODO
            # check if it is in the right place
            else:
                trimmed = Parser.getText(el)
                if trimmed.startswith("(") and trimmed.endswith(")"):
                    Parser.remove(el)


class StandardOutputFormatter(OutputFormatter):
    pass
