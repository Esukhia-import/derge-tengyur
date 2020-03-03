#!/usr/bin/env python3

# The MIT License (MIT)
# Copyright (c) 2018 Esukhia
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

# check xml validity with:
# find . -name "*.xml" -type f -exec xmllint --noout '{}' \;

import re
import os
import time

TEI_BEGINNING = """<?xml version="1.0" encoding="UTF-8"?>
<tei:TEI xmlns:tei="http://www.tei-c.org/ns/1.0">
  <tei:teiHeader>
    <tei:fileDesc>
      <tei:titleStmt>
        <tei:title>{title} [{volnum}]</tei:title>
      </tei:titleStmt>
      <tei:publicationStmt>
        <tei:distributor>Etext proofread by Esukhia, 2015-2018. This TEI files has been automatically generated by a script from text files available on https://github.com/Esukhia/derge-tengyur</tei:distributor>
        <tei:idno type="TBRC_TEXT_RID">UT23703-1{ignum}-0000</tei:idno>
        <tei:idno type="page_equals_image">page_equals_image</tei:idno>
      </tei:publicationStmt>
      <tei:sourceDesc>
        <tei:bibl>
          <tei:idno type="TBRC_RID">W23703</tei:idno>
          <tei:idno type="SRC_PATH">eTengyur/W23703/sources/W23703-1{ignum}/W23703-1{ignum}-0000.txt</tei:idno>
        </tei:bibl>
      </tei:sourceDesc>
    </tei:fileDesc>
  </tei:teiHeader>
  <tei:text>
    <tei:body>
      <tei:div>
        <tei:p n="3" data-orig-n="1a">{title}"""

TEI_END = """</tei:p>
      </tei:div>
    </tei:body>
  </tei:text>
</tei:TEI>
"""

PAREN_RE = re.compile(r"\(([^\),]*),([^\),]*)\)")

def parrepl(match, mode, filelinenum):
    first = match.group(1)
    sec = match.group(2)
    return mode == 'first' and first or sec

def tohrepl(match):
    toh = match.group(1)
    #return '<tei:milestone unit="text" toh="'+toh+'"/>'
    # we don't want xml tags for texts (yet)
    return '' 

def parse_one_line(line, filelinenum, state, outf, volnum, options):
    if filelinenum == 1:
        return
    if filelinenum == 2:
        ignum = volnum + 316
        title = ""
        if line.startswith("[1a.1]"):
            title = line[6:]
        header = TEI_BEGINNING.format(title = title, volnum = volnum, ignum = ignum)
        outf.write(header)
        state['pageseqnum']= 3
        state['pagestr'] = "1a"
        if line.startswith("[1a.1]"):
            return
    pagelinenum = ''
    endpnumi = line.find(']')
    if endpnumi == -1:
        print("error on line "+str(filelinenum)+" cannot find ]")
        return
    pagelinenum = line[1:endpnumi]
    newpage = False
    linenumstr = ''
    pagestr = pagelinenum
    doti = pagelinenum.find('.')
    if doti != -1:
        pagestr = pagelinenum[:doti]
        linenumstr = pagelinenum[doti+1:]
    if 'pagestr' in state:
        oldpagestr = state['pagestr']
        if oldpagestr != pagestr:
            newpage = True
    if newpage:
        state['pageseqnum']+= 1
    state['pagestr']= pagestr
    text = ''
    if len(line) > endpnumi+1:
        text = line[endpnumi+1:]
        text = text.replace('&', '')
        text = text.replace('#', '')
        if '{D' in text:
            text = re.sub(r"\{D([^}]+)\}", lambda m: tohrepl(m), text)
        if 'keep_errors_indications' not in options or not options['keep_errors_indications']:
            text = text.replace('[', '').replace(']', '')
        if 'fix_errors' not in options or not options['fix_errors']:
            text = re.sub(r"\(([^\),]*),([^\),]*)\)", lambda m: parrepl(m, 'second', filelinenum), text)
        else:
            text = re.sub(r"\(([^\),]*),([^\),]*)\)", lambda m: parrepl(m, 'first', filelinenum), text)
    if newpage:
        outf.write('</tei:p>\n        <tei:p n="'+str(state['pageseqnum'])+'" data-orig-n="'+pagestr+'">')
    if text != '':
        outf.write('<tei:milestone unit="line" n="'+linenumstr+'"/>'+text)

def parse_one_file(infilename, outfilename, volnum, options):
    with open(infilename, 'r', encoding="utf-8") as inf:
        with open(outfilename, 'w', encoding="utf-8") as outf:
            state = {}
            linenum = 1
            for line in inf:
                if linenum == 1:
                    line = line[1:]# remove BOM
                # [:-1]to remove final line break
                parse_one_line(line[:-1], linenum, state, outf, volnum, options)
                linenum += 1
            outf.write(TEI_END)

if __name__ == '__main__':
    """ Example use """
    options = {
        "fix_errors": False,
        "keep_errors_indications": False
    }
    #parse_one_file('../derge-kangyur-tags/102-tagged.txt', '/tmp/test.xml', 1, options)
    os.makedirs('./output/', exist_ok=True)
    versionTag = f'UT23703-{time.strftime("%y%m%d")}'
    volnumfilemapping = {}
    for fname in os.listdir('../text/'):
        volnum = int(fname[:3])
        volnumfilemapping[volnum] = fname
    for volnum in range(1, 213):
        volnumstr = '{0:03d}'.format(volnum)
        if volnum not in volnumfilemapping:
            print("no file found for volume "+str(volnum))
            continue
        infilename = '../text/'+volnumfilemapping[volnum]
        print("transforming "+infilename)
        os.makedirs(f'./output/{versionTag}/UT23703-1'+str(volnum+316), exist_ok=True)
        parse_one_file(infilename, f'./output/{versionTag}/UT23703-1'+str(volnum+316)+'/UT23703-1'+str(volnum+316)+'-0000.xml', volnum, options)
