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
import lxml.html
from lxml import etree
from copy import deepcopy
from goose.text import innerTrim
from goose.text import encodeValue
from HTMLParser import HTMLParser
import re

goodInlineTags = ['b','strong','em','i','a','img','big','cite','code','q','s','small','strike','sub','tt','u','var']
badInlineTags = ['abbr','acronym','basefont','bdo','dfn','font','input','kbd','label','samp','select','span','textarea','sup']
goodBlockTags = ['p','h1','h2','h3','h4','h5','h6','blockquote']

class Parser(object):

    @classmethod
    def fromstring(self, html):
        html = encodeValue(html)
        try:
            self.doc = lxml.html.fromstring(html)
        except:
            html = html.encode('utf-8','replace')
            self.doc = lxml.html.fromstring(html)
        return self.doc

    @classmethod
    def nodeToString(self, node):
        return etree.tostring(node)

    @classmethod
    def replaceTag(self, node, tag):
        node.tag = tag

    @classmethod
    def stripTags(self, node, *tags):
        etree.strip_tags(node, *tags)

    @classmethod
    def getElementById(self, node, idd):
        selector = '//*[@id="%s"]' % idd
        elems = node.xpath(selector)
        if elems:
            return elems[0]
        return None

    @classmethod
    def getElementsByTag(self, node, tag=None, attr=None, value=None, childs=False):
        NS = "http://exslt.org/regular-expressions"
        # selector = tag or '*'
        selector = 'descendant-or-self::%s' % (tag or '*')
        if attr and value:
            selector = '%s[re:test(@%s, "%s", "i")]' % (selector, attr, value)
            #selector = '%s[%s="%s"]' % (selector, attr, value)
        #elems = node.cssselect(selector)
        elems = node.xpath(selector, namespaces={"re": NS})
        # remove the root node
        # if we have a selection tag
        if node in elems and (tag or childs):
            elems.remove(node)
        return elems

    @classmethod
    def appendChild(self, node, child):
        node.append(child)

    @classmethod
    def childNodes(self, node):
        return list(node)

    @classmethod
    def childNodesWithText(self, node):
        root = node
        # create the first text node
        # if we have some text in the node
        if root.text:
            t = lxml.html.HtmlElement()
            t.text = root.text
            t.tag = 'text'
            root.text = None
            root.insert(0, t)
        # loop childs
        for c, n in enumerate(list(root)):
            idx = root.index(n)
            # don't process texts nodes
            if n.tag == 'text':
                continue
            # create a text node for tail
            if n.tail:
                t = self.createElement(tag='text', text=n.tail, tail=None)
                n.tail = None
                root.insert(idx + 1, t)
        return list(root)

    @classmethod
    def textToPara(self, text):
        return self.fromstring(text)

    @classmethod
    def getElementsByTags(self, node, tags):
        selector = ','.join(tags)
        elems = node.cssselect(selector)
        # remove the root node
        # if we have a selection tag
        if node in elems:
            elems.remove(node)
        return elems

    @classmethod
    def createElement(self, tag='p', text=None, tail=None):
        t = lxml.html.HtmlElement()
        t.tag = tag
        t.text = text
        t.tail = tail
        return t

    @classmethod
    def getComments(self, node):
        return node.xpath('//comment()')

    @classmethod
    def getParent(self, node):
        return node.getparent()

    @classmethod
    def remove(self, node):
        parent = node.getparent()
        if parent is not None:
            if node.tail:
                prev = node.getprevious()
                if prev is None:
                    if not parent.text:
                        parent.text = ''
                    parent.text += u' ' + node.tail
                else:
                    if not prev.tail:
                        prev.tail = ''
                    prev.tail += u' ' + node.tail
            node.clear()
            parent.remove(node)

    @classmethod
    def getTag(self, node):
        return node.tag

    @classmethod
    def getText(self, node):
        txts = [i for i in node.itertext()]
        return innerTrim(u' '.join(txts).strip())

    @classmethod
    def clearText(self, text):
        if text == None: return ''
        t = HTMLParser().unescape(text).strip('\t\r\n')
        t = re.sub('[\t\r\n]',' ',t)
        rt = ''; ps = ''
        for s in t:
            if s != ' ' or ps != ' ': rt += s
            ps = s
        pars = rt.split(u'\ufffc')
        return '\n'.join(pars)

    @classmethod
    def getFormattedText(self, node, isTop = True):
        text = ''
        isBlock = False
        badInline = False
        if node.tag in goodInlineTags: pass
        elif node.tag in badInlineTags: badInline = True
        else: # block node
            text = '\n'
            isBlock = True
        node.text = Parser.clearText(node.text)
        text += node.text
        for n in node: text += Parser.getFormattedText(n, False)
        if isBlock: text += '\n'
        if not isTop: 
            node.tail = Parser.clearText(node.tail)
            text += node.tail
        else: text = re.sub(u'[\u2028]',u'',text)
        if badInline and not isTop: node.drop_tag()
        return text

    @classmethod
    def previousSiblings(self, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=True)):
            nodes.append(n)
        return nodes

    @classmethod
    def previousSibling(self, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=True)):
            nodes.append(n)
            if c == 0:
                break
        return nodes[0] if nodes else None

    @classmethod
    def nextSibling(self, node):
        nodes = []
        for c, n in enumerate(node.itersiblings(preceding=False)):
            nodes.append(n)
            if c == 0:
                break
        return nodes[0] if nodes else None

    @classmethod
    def isTextNode(self, node):
        return True if node.tag == 'text' else False

    @classmethod
    def getAttribute(self, node, attr=None):
        if attr:
            return node.attrib.get(attr, None)
        return attr

    @classmethod
    def setAttribute(self, node, attr=None, value=None):
        if attr and value:
            node.set(attr, value)

    @classmethod
    def outerHtml(self, node):
        e0 = node
        if e0.tail:
            e0 = deepcopy(e0)
            e0.tail = None
        return self.nodeToString(e0)

    @classmethod
    def getPath(self, node):
        path = []
        if node.getparent() is not None:
            path = Parser.getPath(node.getparent())
        return [node.tag] + path

    @classmethod
    def adjustTopNode(self, article):
        if article.topNode.getparent() == None:
            e = lxml.html.HtmlElement(); e.tag = 'div';
            e.append(article.topNode)
        Parser.customizeBlocks(article.topNode)

    @classmethod
    def removeTitle(self,n,title,lines = 10):
        if n.tag == 'h1':
            pr = n.getprevious()
            p = n.getparent()
            while pr != None:
                np = pr; pr = pr.getprevious()
                p.remove(np)
            p.text = None
            Parser.remove(n)
            return 0
        lines -= 1;
        if lines <= 0: return 0
        if n.tag in goodBlockTags and n.text != None:
            text = Parser.clearText(n.text).strip()
            if len(text) > 5 and title == text: Parser.remove(n)
        for c in n:
            lines = Parser.removeTitle(c,title,lines)
            if lines <= 0: return 0
        return lines

    @classmethod
    def insertBrs(self,n,pos,lst):
        for t in lst:
            e = lxml.html.HtmlElement(); e.tag = 'br'; e.tail = t
            n.insert(pos,e)

    @classmethod
    def isEmpty(self,e):
        if len(e) == 0 and e.tag != 'br':
            if (e.text is None or re.search('[^ \xa0]',e.text) == None): 
                if (e.tail is None or re.search('[^ \xa0]',e.tail) == None):
                    return True
        return False

    @classmethod
    def customizeBlocks(self, p, mc = True):
        if p.tag not in goodBlockTags and p.tag not in goodInlineTags and p.tag != 'br': p.tag = 'p'
        if p.text is not None: 
            pars = p.text.split('\n')
            if len(pars) > 1:
                p.text = pars[0]
                lst = pars[1:]; lst.reverse()
                Parser.insertBrs(p,0,lst)
        if p.tail is not None: 
            pars = p.tail.split('\n')
            if len(pars) > 1:
                p.tail = pars[0]
                lst = pars[1:]; lst.reverse()
                pp = p.getparent()
                Parser.insertBrs(pp,pp.index(p)+1,lst)
        if len(p) == 0: return
        n = list(p)[0]
        while n is not None:
            if not mc and n.tag not in goodInlineTags and p.tag != 'blockquote' and n.tag != 'br': # block in text block, fix needed
                ni = p.index(n)
                t = p.tail; p.tail = None
                p.remove(n)
                p.addnext(n)
                if n.tag not in goodBlockTags: n.tag = 'p'
                e = lxml.html.HtmlElement(); e.tag = 'div'; e.tail = t; e.text = n.tail; n.tail = None
                n.addnext(e)
                lst = list(p)[ni:]
                for el in lst:
                    p.remove(el)
                    e.append(el)
                return
            Parser.customizeBlocks(n, False)
            np = n; n = n.getnext()
            if np.tag == 'br' and p.tag == 'p':
                ni = p.index(np)
                if ni == 0 and (p.text is None or re.search('[^ \xa0]',p.text) == None): 
                    Parser.remove(np)
                    continue
                elif ni == len(p) - 1 and (np.tail is None or re.search('[^ \xa0]',np.tail) == None): 
                    Parser.remove(np)
                    continue
            if np.tag in goodInlineTags:
                if np.text is None and len(np) == 0: Parser.remove(np)
            elif n != None and n.tag != 'br':
                if Parser.isEmpty(np) and n.tag not in goodInlineTags: np.drop_tag()
        return
