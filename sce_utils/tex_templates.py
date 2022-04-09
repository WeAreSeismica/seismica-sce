import os, sys

def set_up_header(fout,title,authors={},affils={},credits={},\
                  dates={'rec':'January 1, 1900','acc':'February 29, 1900','pub':'April 1, 1900'},\
                  edname='A. Editor',doi='10.100',volume=0,issue=None,\
                  review=True,onecol=False,fast=False,anon=False,\
                  other_langs=[]):
    """
    write out the basic seismica latex header
    fout is an open file handler ready for writing this header
    """
    # set up general options for the template
    docops = ''
    if review: docops += 'review,'
    if onecol: docops += 'onecolumn,'
    if fast: docops += 'fastreport,'
    if anon: docops += 'anonymous,'
    docops = docops[:-1]  # remove trailing comma

    header1 = """% Seismica LuaLatex Template
%!TEX TS-program = lualatex
%!TEX encoding = UTF-8 Unicode
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\documentclass["""+docops+"""]{seismica} 
\\title{"""+title+"""}

\\receiveddate{"""+dates['rec']+"""}
\\accepteddate{"""+dates['acc']+"""}
\publisheddate{"""+dates['pub']+"""}
\editorname{"""+edname+"""}

\doi{"""+doi+"""}
\\thevolume{"""+str(volume)+"""}

"""
    fout.write(header1)

    # parse authors and affiliations
    for k in authors.keys():
        auth = authors[k]
        towrite = '\\author['+auth['supers']+']{'+auth['name']
        if 'orcid' in auth.keys():
            towrite += '\n\orcid{'+auth['orcid']+'}'
        if 'corresp' in auth.keys():
            towrite += '\n\\thanks{Corresponding author: '+auth['corresp']+'}'
        towrite += '}\n'
        fout.write(towrite)
    fout.write('\n')

    for k in affils.keys():
        aff = affils[k]
        fout.write('\\affil['+aff['super']+']{'+aff['place']+'}\n')
    fout.write('\n')

    for k in credits.keys():
        fout.write('\credit{'+k+'}{'+credits[k]+'}\n')
    fout.write('\n')

    if len(other_langs) > 0:
        header2 = '\\setotherlanguages{'
        for l in other_langs:
            header2 += '%s,' % l
        header2 = header2[:-1]
        header2 += '}'
        fout.write(header2)
        fout.write('\n')

    fout.write('\\begin{document}')

    return fout

def add_abstracts(fout,summaries):
    """
    write abstract(s) and optional non-technical summary into file after header
    """
    towrite = """
\makeseistitle{\n"""
    for k in summaries.keys():
        abst = summaries[k]
        toadd = ''
        if abst['language'] != 'English':
            toadd += "\\begin{%s}\n" % abst['language']
        toadd += "\\begin{summary}{%s}\n" % abst['name']
        toadd += "%s\n\end{summary}\n" % abst['text']
        if abst['language'] != 'English':
            toadd += "\end{%s}\n" % abst['language']
        towrite += toadd

    towrite += "}\n"
    fout.write(towrite)

    return fout


