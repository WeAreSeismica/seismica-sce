import os, sys

def set_up_header(fout,title,authors={},affils={},\
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

    for k in affils.keys():
        aff = affils[k]
        fout.write('\\affil['+aff['super']+']{'+aff['place']+'}\n')

    if len(other_langs) > 0:
        header2 = '\\setotherlanguages{'
        for l in other_langs:
            header2 += '%s,' % l
        header2 = header2[:-1]
        header2 += '}'
        fout.write(header2)

    fout.write('\\begin{document}')

    return fout

def add_abstract(fout,abs1,abs2=None,abs2_dict={},abs3=None,abs3_dict={}):
    """
    write abstract(s) into file after header
    """
    towrite = """
\makeseistitle
{
\\begin{summary}{Abstract}"""+abs1+"""
\end{summary}
}
"""
    fout.write(towrite)

    if abs2 is not None:
        towrite = """{
\\begin{"""+abs2_dict['language']+"""}
\\begin{summary}{"""+abs2_dict['name']+"""}"""+abs2+"""
\end{summary}
\end{"""+abs2_dict['language']+"""}
}
"""
    else:
        towrite = '{}'
    fout.write(towrite)

    if abs3 is not None:
        towrite = """{
\\begin{"""+abs3_dict['language']+"""}
\\begin{summary}{"""+abs3_dict['name']+"""}"""+abs3+"""
\end{summary}
\end{"""+abs3_dict['language']+"""}
}
"""
    else:
        towrite = '{}'
    fout.write(towrite)

    return fout


