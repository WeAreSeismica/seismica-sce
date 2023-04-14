import os, sys, datetime

def set_up_header(fout,title,authors={},affils={},credits={},\
                  anon=False,langs=False,breakmath=False,preprint=False,\
                  other_langs=[]):
    """
    write out the basic seismica latex header
    fout is an open file handler ready for writing this header
    """
    # set up general options for the template
    docops = 'proof,'  # start with this default for conversion, easy to remove
    if anon: docops += 'anonymous,'
    if langs: docops += 'languages,'
    if breakmath: docops += 'breakmath,'
    if preprint: docops += 'preprint,'
    docops = docops[:-1]  # remove trailing comma

    header1 = """% Seismica Publication Template
% LuaLatex

%! TEX TS-program = lualatex
%! TEX encoding = UTF-8 Unicode
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% options: report, breakmath, proof, onecolumn, invited
\documentclass["""+docops+"""]{seismica} 

% if a report, specify report type:
%\\reportheader{Fast Report}
%\\reportheader{Null Results Report}
%\\reportheader{Software Report}
%\\reportheader{Instrument Deployment Report}
%\\reportheader{Field Campaign Report}

% SCE team metadata:
\dois{10.0000/issn-issn}
\\receiveddate{DATE HERE}
\\accepteddate{DATE HERE}
\publisheddate{DATE HERE}
\\theyear{"""+str(datetime.datetime.now().year)+"""}
\\thevolume{0}
\\thenumber{0}
\prodedname{the production editor}
\handedname{the handling editor}
\copyedname{the copy/layout editor}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\title{"""+title+"""}
\shorttitle{"""+title+"""}

"""
    fout.write(header1)

    # parse authors and affiliations
    for ik,k in enumerate(authors.keys()):
        auth = authors[k]
        towrite = '\\author['+auth['supers']+']{'+auth['name']
        if ik > 0:
            towrite = towrite.replace(' ','~')
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
        header2 = """\\usepackage{polyglossia}
\\usepackage{fontspec}
\\setmainlanguage[]{english}
\\setotherlanguages{
"""
        for l in other_langs:
            header2 += '%s,' % l
        header2 = header2[:-1]
        header2 += """}\n
%\\newfontfamily\thaifont[Script=Thai]{Noto Serif Thai}
%% also see https://www.overleaf.com/latex/examples/how-to-write-multilingual-text-with-different-scripts-in-latex/wfdxqhcyyjxz for reference

"""
        fout.write(header2)

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


