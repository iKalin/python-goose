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
import re
import string
from array import array
import os.path
from goose.utils import FileHelper
from goose.utils.encoding import smart_unicode
from goose.utils.encoding import smart_str
from goose.utils.encoding import DjangoUnicodeDecodeError

TABSSPACE = re.compile(r'[\s\t]+')
TRANS_TABLE = string.maketrans(string.punctuation.replace("'",""), ' '*(len(string.punctuation)-1))

def innerTrim(value):
    if isinstance(value, (unicode, str)):
        # remove tabs and new lines
        return TABSSPACE.sub(u' ', value).replace(u'\r',u'').replace(u'\n',u'').strip()
    return ''


def encodeValue(value):
    string_org = value
    try:
        value = smart_unicode(value)
    except (UnicodeEncodeError, DjangoUnicodeDecodeError):
        value = smart_str(value)
    except:
        value = string_org
    return value

lang_codes = array('c','\x00'*65536)
lang_map = {}
lang_num = 1
unilang2iso = {
    'Greek':'el', 'Georgian':'ka', 'Armenian':'hy', 'Arabic':'ar', 'Telugu':'te',
    'Thai':'th', 'Mongolian':'mn', 'Avestan':'ae', 'Bengali':'bn', 'Tamil':'ta',
    'Sinhala':'si', 'Khmer':'km', 'Sundanese':'su', 'Hebrew':'he', 'Oriya':'or',
    'Malayalam':'ml', 'Tibetan':'bo', 'Tagalog':'tl', 'Gujarati':'gu', 'Kannada':'kn',
    'Lao':'lo', 'Javanese':'jv',
}

def load_unicode_script():
    global lang_codes, lang_map, lang_num
    data_path = os.path.join(os.path.dirname(__file__), "resources/unicode/Scripts.txt")
    f = open(data_path,'rb')
    lang_map_r = {}
    for l in f:
        if l[0] == "#" or len(l) < 10: continue
        spl = l.partition(';')
        if not spl[2]: continue
        lang = spl[2].partition("#")[0].strip()
        if lang not in lang_map_r:
            lang_map_r[lang] = chr(lang_num)
            lang_num += 1
        lang = lang_map_r[lang]
        urange = spl[0].strip().partition("..")
        bc = int(urange[0],16)
        if bc > 65535: continue
        if not urange[2]: ec = bc + 1
        else: ec = int(urange[2],16) + 1
        for c in xrange(bc,ec):
            lang_codes[c] = lang
    f.close()
    lang_codes = lang_codes.tostring()
    for l in lang_map_r: lang_map[lang_map_r[l]] = l
    lang_map['\x00'] = "undefined"
load_unicode_script()

def get_languages(txt):
    langs = {}
    lang_match = [0]*lang_num
    txt_len = len(txt)
    for c in txt:
        code = ord(c)
        if code > 65535: continue
        lang_match[ord(lang_codes[code])] += 1
    lang_match = [(lang_match[i],chr(i)) for i in xrange(lang_num)]
    lang_match.sort()
    lang_match.reverse()
    for l in lang_match:
        if l[0] < 10 or l[0] < txt_len*0.01: break
        txt_len -= l[0]
        langs[lang_map[l[1]]] = l[0]
    result = []
    # cjk detection
    chinese = langs.get('Han',0)
    japan = langs.get('Hiragana',0) + langs.get('Katakana',0)
    korean = langs.get('Hangul',0)
    if korean and korean > chinese*0.1 and korean > japan: result.append('ko')
    elif japan and japan > chinese*0.1 and japan > korean: result.append('ja')
    elif chinese: result.append('zh')
    # some other unicode languages detection
    for k in langs:
        if k in unilang2iso: result.append(unilang2iso[k])
    return result

class WordStats(object):

    def __init__(self):
        # total number of stopwords or
        # good words that we can calculate
        self.stopWordCount = 0

        # total number of words on a node
        self.wordCount = 0

        # holds an actual list
        # of the stop words we found
        self.stopWords = []

    def getStopWords(self):
        return self.stopWords

    def setStopWords(self, words):
        self.stopWords = words

    def getStopWordCount(self):
        return self.stopWordCount

    def setStopWordCount(self, wordcount):
        self.stopWordCount = wordcount

    def getWordCount(self):
        return self.wordCount

    def setWordCount(self, cnt):
        self.wordCount = cnt


class StopWords(object):

    _cached_stop_words = {}

    def __init__(self, language='en'):
        # TODO replace 'x' with class
        # to generate dynamic path for file to load
        if isinstance(language,str): language = [language]
        language = set(language)
        self.char_split = False
        if 'zh' in language or 'ko' in language or 'ja' in language: self.char_split = True
        self.STOP_WORDS = None
        for l in language:
            if not l in StopWords._cached_stop_words:
                path = 'text/stopwords-%s.txt' % l
                try:
                    _stop_list = FileHelper.loadResourceFile(path)
                    if l in ['zh','ko','ja']: _stop_list = _stop_list.decode('utf-8')
                    StopWords._cached_stop_words[l] = set(_stop_list.splitlines())
                except:
                    StopWords._cached_stop_words[l] = set()
            if self.STOP_WORDS is None: self.STOP_WORDS = StopWords._cached_stop_words[l]
            else: self.STOP_WORDS |= StopWords._cached_stop_words[l]

    def removePunctuation(self, content):
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        return content.translate(TRANS_TABLE, '')

    def candiate_words(self, stripped_input):
        return stripped_input.split(' ')

    def getStopWordCount(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        strippedInput = self.removePunctuation(content)
        strippedInput = strippedInput.replace('\xc2\xa0',' ').lower()
        candidateWords = self.candiate_words(strippedInput)
        overlappingStopWords = []
        for w in candidateWords:
            if w in self.STOP_WORDS:
                overlappingStopWords.append(w)

        if self.char_split:
            for w in content:
                if w in self.STOP_WORDS:
                    overlappingStopWords.append(w)

        ws.setWordCount(len(candidateWords))
        ws.setStopWordCount(len(overlappingStopWords))
        ws.setStopWords(overlappingStopWords)
        return ws

class StopWordsChinese(StopWords):
    """
    Chinese segmentation
    """
    def __init__(self, language='zh'):
        # force zh languahe code
        super(StopWordsChinese, self).__init__(language='zh')

    def candiate_words(self, stripped_input):
        # jieba build a tree that takes sometime
        # avoid building the tree if we don't use
        # chinese language
        import jieba
        return jieba.cut(stripped_input, cut_all=True)


class StopWordsArabic(StopWords):
    """
    Arabic segmentation
    """
    def __init__(self, language='ar'):
        # force ar languahe code
        super(StopWordsArabic, self).__init__(language='ar')

    def remove_punctuation(self, content):
        return content

    def candiate_words(self, stripped_input):
        import nltk
        s = nltk.stem.isri.ISRIStemmer()
        words = []
        for word in nltk.tokenize.wordpunct_tokenize(stripped_input):
            words.append(s.stem(word))
        return words

