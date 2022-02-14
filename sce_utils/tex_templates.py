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


_latex_special_chars = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '\n': '\\newline%\n',
    '-': r'{-}',
    '\xA0': '~',  # Non-breaking space
    '[': r'{[}',
    ']': r'{]}',
}

class NoEscape(str):
    """
    A simple string class that is not escaped.
    When a `.NoEscape` string is added to another `.NoEscape` string it will
    produce a `.NoEscape` string. If it is added to normal string it will
    produce a normal string.
    Args
    ----
    string: str
        The content of the `NoEscape` string.
    """

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self)

    def __add__(self, right):
        s = super().__add__(right)
        if isinstance(right, NoEscape):
            return NoEscape(s)
        return s

def escape_latex(s):
    r"""Escape characters that are special in latex.
    Args
    ----
    s : `str`, `NoEscape` or anything that can be converted to string
        The string to be escaped. If this is not a string, it will be converted
        to a string using `str`. If it is a `NoEscape` string, it will pass
        through unchanged.
    Returns
    -------
    NoEscape
        The string, with special characters in latex escaped.
    Examples
    --------
    >>> escape_latex("Total cost: $30,000")
    'Total cost: \$30,000'
    >>> escape_latex("Issue #5 occurs in 30% of all cases")
    'Issue \#5 occurs in 30\% of all cases'
    >>> print(escape_latex("Total cost: $30,000"))
    References
    ----------
        * http://tex.stackexchange.com/a/34586/43228
        * http://stackoverflow.com/a/16264094/2570866
    """

    if isinstance(s, NoEscape):
        return s

    return NoEscape(''.join(_latex_special_chars.get(c, c) for c in str(s)))
