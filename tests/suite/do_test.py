from lxml import etree
import re
import codecs
import os
import base64
import commands
import json
import time
import sys
from StringIO import StringIO
try:
    from readability.readability import Document
except:
    print "Error loading python-readability module"
try:
    from boilerpipe.extract import Extractor
except:
    print "Error loading python-boilerpipe module"
try:
    from goose.Goose import Goose
except:
    print "Error loading python-goose module"

EXTRACTOR = 'goosepy'
folder = '.'

def ext_goosepy(html):
    g = Goose()
    g.config.enableImageFetching = False
    article = g.extractContent(url="http://www.example.com/test.html", rawHTML=html)
    return article.cleanedArticleText 

def ext_boilerpipe(html):
    extractor = Extractor(extractor='ArticleExtractor', html=html)
    text = extractor.getText()
    return text

def ext_readability(html):
    text = Document(html).summary()
    parser = etree.HTMLParser()
    test = etree.parse(StringIO(text), parser)
    r = test.xpath("//text()")
    h = ""
    for rr in r:
        text = rr.encode('ascii', 'replace')
        h += text + "\n"
    return h

def getfilteredhtml(fname):
    parser = etree.HTMLParser()
    test = etree.parse(folder + "/original/" + fname, parser)
    html = etree.tostring(test,method='text',encoding=unicode)
    html = re.sub(u'[\u2028]',u'',html)
    html = html.encode('ascii', 'replace')
    html = re.sub('[.?,\'\t\r\n]',' ',html)
    html = html.split()
    html = ' '.join(html)
    return html

def getrawhtml(fname):
    f = open(folder +"/original/" + fname,'rb')
    flines = f.readlines()
    f.close()
    html = ""
    for line in flines:
        html += line
    return html

def gettext(html):
    text = html.encode('ascii', 'replace')
    text = re.sub('[.?,\'\t\r\n]',' ',text)
    text = text.split()
    text = ' '.join(text)
    return text

def createstats(html, root, sel, f, fname):
    r = root.xpath(sel)
    lost_words = 0
    lost_len = 0
    found_words = 0
    found_len = 0
    for rr in r:
         if rr.text is None: continue
	 text = re.sub(u'[\u2028]',u'',rr.text)
         text = text.encode('ascii', 'replace')
         texts = text.split('\n')
         for text in texts:
             text = re.sub('[.?,\'\t\r\n]',' ',text)
             text = text.split()
             text = ' '.join(text)
             if html.find(text)<0:
                 if f is not None: f.write(fname + ' lost: ' + text + '\n')
                 lost_words += len(text.split())
                 lost_len += len(text)
             else:
                 if text: html = ' '.join(html.split(text,1))
                 found_words += len(text.split())
                 found_len += len(text)
    return [lost_words, lost_len, found_words, found_len, html]


extractors = {'goosepy': ext_goosepy, 'readability': ext_readability, 'boilerpipe': ext_boilerpipe}

def checkfile(fname, f):
#    print fname

    if EXTRACTOR == "raw": html = getfilteredhtml(fname)
    else:
        html = getrawhtml(fname)
        html = gettext(extractors[EXTRACTOR](html))

    lost_words = 0;
    lost_len = 0;
    excess_words = len(html.split())
    excess_len = len(html)
    suppl_words = 0
    suppl_len = 0
    total_words = excess_words
    total_len = excess_len
    etalon_words = 0
    html1 = html

    parser = etree.HTMLParser()
    root = etree.parse(folder + "/annotated/" + fname, parser)
#    print html
    res = createstats(html, root, "//*[@class='x-nc-sel2']", f, fname)
    html = res[4]
    etalon_words = res[0]+res[2]
    lost_words += res[0]
    lost_len += res[1]
    excess_words -= res[2]
    excess_len -= res[3]
    res = createstats(html, root, "//*[@class='x-nc-sel1']", None, fname)
    html = res[4]
    excess_words -= res[2]
    excess_len -= res[3]
    suppl_words += res[2]
    suppl_len +=res[3]
    res = createstats(html, root, "//*[@class='x-nc-sel3']", None, fname)
    html = res[4]
    excess_words -= res[2]
    excess_len -= res[3]
    suppl_words += res[2]
    suppl_len +=res[3]
    if f is not None and re.search('[^ \t\r\n]',html): f.write(fname + ' excess: ' + html.strip() + '\n')
    if excess_words < 0: 
        excess_words = 0
        excess_len = 0
#    if etalon_words > 0 and lost_words > 0 and 1.0*lost_words/etalon_words > 0.1: 
#        print fname
#        print html
#        print lost_words
#        print etalon_words
#    elif etalon_words > 0 and 1.0*excess_words/etalon_words > 0.2:
#        print fname
#        print html
    if etalon_words == 0: print "Empty etalon file: " + fname
    if lost_words != 0 or excess_words != 0: f.write('-'*60 + '\n' + html1 + '\n' + '-'*60 + '\n')
    return [lost_words,lost_len,excess_words,excess_len,suppl_words,suppl_len,total_words,total_len,etalon_words]


def test():
    global folder
    folder = sys.argv[1]
    listing = os.listdir(folder +'/original')
    lost_words = 0;
    lost_len = 0;
    excess_words = 0;
    excess_len = 0;
    truncated = 0;
    suppl_words = 0
    suppl_len = 0
    exceptions = 0
    total_words = 0
    total_len = 0
    exact_match = 0
    near_exact_match = 0
    low_loss = 0
    etalon_words = 0

    f = codecs.open("lost_lines.txt",'wb','utf-8')
    btime = time.time();
    for fname in listing:
#        try:
        res = checkfile(fname,f)
#        except:
#            exceptions += 1
#            res = [0,0,0,0,0,0,0,0,0]
#            print "Extractor exception, file: " + fname
        lost_words += res[0];
        lost_len += res[1];
        excess_words += res[2];
        excess_len += res[3];
        suppl_words += res[4];
        suppl_len += res[5];
        total_words += res[6];
        total_len += res[7];
        if res[0] != 0: truncated += 1;
        if res[2] <= 0 and res[0] == 0: exact_match += 1;
        if res[0] == 0 and res[2] > 0 and res[8] > 0 and 1.0*res[2]/res[8] < 0.2:
            near_exact_match += 1;
            print "Near exact match file: " + fname
        if res[0] > 0 and res[8] > 0 and 1.0*res[0]/res[8] < 0.1: 
            low_loss += 1;
            print "Low loss file: " + fname
        elif res[0] > 0:
            print "Truncated file: " + fname

    etime = time.time();
    f.close()
    truncated -= low_loss

    print "Total amount: %d words %d chars" % (total_words,total_len)
    print "Lost: %d words %d chars" % (lost_words,lost_len)
    print "Excess: %d words %d chars" % (excess_words,excess_len)
    print "Supplement: %d words %d chars" % (suppl_words,suppl_len)
    print "Truncated: %d pages" % (truncated+exceptions)
    print "Exact match: %d pages" % (exact_match-exceptions)
    print "Near exact match (excess<0.2): %d pages" % (near_exact_match)
    print "Low loss (loss<0.1): %d pages" % (low_loss)
    print "Documents processed: %d pages" % (len(listing))
#    print "Exceptions: %d pages" % (exceptions)
    print "Elapsed time: %d sec" % (etime - btime)
