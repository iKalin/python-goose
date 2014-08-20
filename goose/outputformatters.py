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
        return self.convertToText(article)

    def convertToText(self,article):
        text = Parser.getFormattedText(self.topNode)
        lines = text.split(u'\n')
        text = u''
        for line in lines:
            if re.search('[^ \xa0]',line): text += line + u'\n'
        Parser.adjustTopNode(article)
        return text

class StandardOutputFormatter(OutputFormatter):
    pass
