import numpy as np
from re import finditer
import os, sys

####
# functions for text processing of pandoc outputs
####

def document_structure(ftex_in):
    """
    read through entire pandoc'd file and extract outline, with line numbers for
    where each section heading is
    this prepares us to get article metadata (author orcids, credit) with fewer assumptions
    about how those sections are ordered (still need authors and title first, though)
    and if we want it could let us check that all necessary sections are in fact present?
    """
    struct = {}
    ftex_in.seek(0)
    nln = sum(1 for line in ftex_in)
    ftex_in.seek(0)
    i = 0  # line counter
    j = 0  # section heading counter
    while i < nln:
        line = ftex_in.readline()
        if line.startswith('\hypertarget'):  # next line will be section heading
            i += 1
            line = ftex_in.readline()  # this will be the heading
            if line.split('{')[1][0].isdigit():
                sname = ' '.join(line.split('{')[1].split('}')[0].split(' ')[1:])
            else:
                sname = line.split('{')[1].split('}')[0]
            sect = {'sname': sname,\
                    'level': line.split('{')[0][1:],\
                    'line':i}
            struct[j] = sect
            j += 1
        elif line.startswith('\\begin{document}'):
            sect = {'sname':'begin_doc',\
                    'level': 0,\
                    'line': i}
            struct['b'] = sect
        i += 1
    return ftex_in, struct

def parse_environment(line,ftex_in,ftex_out,fjunk,nequ,nfig,ntab):
    """
    read and deal with an environment (equation, figure, table)
    """
    print('environment detected')  # notify the user that we found something
    temp = [line]
    while True:
        line = ftex_in.readline()
        temp.append(line)
        if line.startswith('\end{'):
            break
    if len(temp) < 10:
        for e in temp: print('\t',e[:-1])  # skip newlines with [:-1]
    else:
        for e in temp[:9]: print('\t',e[:-1])

    ieq = input('is this an [e]quation, [f]igure, [t]able, or [n]one of the above?') or 'n' # ask if it looks like an equation
    print('\n')
    if ieq.lower() == 'e':  # if it does, parse it like one
        ftex_out.write('\\begin{equation}\n')
        for k in range(0,len(temp)):  # this only matters if someone puts their equations in tables
            if temp[k].startswith('\\toprule') or temp[k].startswith('\endhead')\
                or temp[k].startswith('\\bottomrule') or temp[k].startswith('\end{')\
                or temp[k].startswith('\\begin{longtable'):
                pass
            elif temp[k].startswith('\('):  # probably the start of the equation
                if '&' in temp[k]:
                    goodpart = temp[k].split('&')[0].rstrip()  # get rid of 2nd column (if table)
                    ftex_out.write(goodpart[2:-2]+'\n')
                else:
                    ftex_out.write(temp[k][2:-2]+'\n') # strip the \( part?
            else:
                ftex_out.write(temp[k])  # split lines? who knows?
        ftex_out.write('\label{eq%i}\n' % nequ)  # label the equation for tex reference
        ftex_out.write('\end{equation}\n')
        nequ += 1  # increment the equation counter

    elif ieq.lower() == 'f':
        ftex_out.write('\\begin{figure}\n')
        ftex_out.write('\includegraphics[width = \columnwidth]{example-image}\n')
        ftex_out.write('\caption{placeholder caption}\n')
        ftex_out.write('\label{fig%i}\n' % nfig)
        ftex_out.write('\end{figure}\n')
        print('moving this environment to junk file; sort it out manually\n')
        fjunk.write('Figure %i\n' % nfig)
        for k in temp:
            fjunk.write(k)
        fjunk.write('\n')  # saving for later
        nfig += 1

    elif ieq.lower() == 't':
        ftex_out.write('\\begin{table}[h]\n')
        ftex_out.write('\centering\n')
        ftex_out.write('\\begin{tabular}{lc}\hline\n')
        ftex_out.write('\\textbf{Data type} & \\textbf{some numbers} \\\\ \hline \n')
        ftex_out.write('type 1 & 1 \\\\ \n')
        ftex_out.write('type 2 & 2 \\\\ \hline \n')
        ftex_out.write('\end{tabular}\n')
        ftex_out.write('\caption{placeholder caption}\n')
        ftex_out.write('\label{tbl%i}\n' % ntab)
        ftex_out.write('\end{table}\n')
        print('moving this environment to junk file; sort it out manually\n')
        fjunk.write('Table %i\n' % ntab)
        for k in temp:
            fjunk.write(k)
        fjunk.write('\n')  # saving for later
        ntab += 1

    else:
        print('moving this environment to junk file; sort it out manually\n')
        fjunk.write('Unspecified thing:\n')
        for k in temp:
            fjunk.write(k)
        fjunk.write('\n')

    return ftex_in, ftex_out, fjunk, nequ, nfig, ntab, ieq

def check_for_fig_tab_eqn_refs(to_write):
    """
    check a line for 'Figure 1' or 'Equation 9' or whatever, replace those with linked refs
    """

    capital_names = ['Figure','Equation','Table','Fig.','Eq.']
    ref_names = ['fig','eq','tbl','fig','eq']

    for iw, word in enumerate(capital_names):
        if word in to_write.split() or '('+word in to_write.split():
            nrefs = len([m.start() for m in finditer(word,to_write)])
            # for each such index, look for the number
            for ireplace in range(nrefs):
                inds = np.array([m.start() for m in finditer(word,to_write)])
                ifig = inds[ireplace]
                shift = len(word) + 1
                try:
                    fig_num = int(to_write[ifig+shift])
                except ValueError:  # this isn't an int
                    if to_write[ifig+shift] == 'S':  # a supplemental item? skip it
                        fig_num = 999
                    else:
                        try:
                            shift = len(word) + 2
                            fig_num = int(to_write[ifig+shift])  # maybe the number was in parens?
                        except ValueError:
                            fig_num = 999

                if fig_num != 999: # check again for double-digit numbers
                    try:           # (if anyone has >99 figures we are in trouble)
                        second_digit = int(to_write[ifig+shift+1])
                        fig_num = int(to_write[ifig+shift:ifig+shift+2])
                    except ValueError:
                        pass  # we were fine to start with

                if fig_num != 999:
                    # replace the word and number with an inline reference 
                    line_start = to_write[:ifig]
                    if fig_num > 9:
                        line_end = to_write[ifig+shift+2:]
                    else:
                        line_end = to_write[ifig+shift+1:]
                    to_write = line_start + word + '~\\ref{%s%i}' % (ref_names[iw],fig_num) + line_end

    return to_write

def get_abstract(ftex_in):
    """
    after finding second- or third-language abstract header, read and parse that abstract
    return abstract text and dict with abstract info (language, heading)
    """
    abs2_dict = {}
    abs2 = ''
    while True:
        line = ftex_in.readline()
        if line.startswith('\section'):
            hdr = line.split('{')[1].split('}')[0].split(':')[-1].lstrip()
            abs2_dict['name'] = hdr.split('(')[0].rstrip()
            abs2_dict['language'] = hdr.split('(')[-1].split(')')[0].lower()
        else:
            if not line.startswith('\hypertarget'):  # until we hit the next section
                abs2 = abs2 + line.rstrip()
            else:
                break 
        abs2_dict['text'] = abs2

    return ftex_in, line, abs2_dict

def print_reminders(ofile_tex):
    print('An output tex file has been written at: %s' % ofile_tex)
    print('Unparsable table/figure info is in junk.tex')
    print('Remember to update metadata in header: editor, volume #, DOI, dates, etc')
    return

########################################################################
# citations
########################################################################

def parse_parentheticals(line,bibkeys):
    """
    for a line of text, parse parentheticals for citations and replace with appropriate \cite calls
    """
    to_write = ''  # for appending pieces of text as they're checked
    if '(' in line:  # check for parentheticals
        # find indices of open/close parens
        open_par = [pos for pos, char in enumerate(line) if char == '(']
        clse_par = [pos for pos, char in enumerate(line) if char == ')']
        if len(open_par) != len(clse_par):
            print('mismatched parentheticals :(')
            print(line)
            sys.exit()

    else:  # no parentheticals in this line of text:
        return line

    # if there are parentheticals, move on to process them
    for k in range(len(open_par)):
        # separate out the parenthetical and the text between this and the previous parenthetical
        paren = line[open_par[k]+1:clse_par[k]]
        if k == 0:
            pretext = line[:open_par[k]]
        else:
            pretext = line[clse_par[k-1]+1:open_par[k]]  # the last bit of text before this parenthetical

        # check if this is inline math
        if pretext[-1] == '\\':
            to_write += pretext
            to_write += line[open_par[k]:clse_par[k]+1]
            break

        # if not math, continue to parse:
        parsed, pretext = _parse_paren(paren,pretext,bibkeys)

        # add the parsed stuff (pre-paren text may be altered for (YYYY) citations)
        to_write += pretext
        to_write += parsed

        if k == len(open_par) - 1:
            to_write += line[clse_par[-1]+1:]

    return to_write


def _parse_paren(paren, pretext, bibkeys):
    """
    parse whatever's in one set of parens
    """

    is_preamble = False  # non-citation text in the parenthetical before the first citation
    is_badref = False    # unparseable for some unknown reason
    is_abamb = False     # more than one paper by this author set for this year; resolve manually
    citations = []       # to hold list of bibkeys
    badtext = ''         # for text if only *some* refs are bad

    # split up the parenthetical by spaces -> this will have all punctuation preserved
    paren = paren.split(' ')

    # find years
    yr_inds = np.where([e[:4].isdigit() for e in paren])[0]

    # CASE: if all the contents are years, figure out citation from pre-paren text
    if len(yr_inds) == len(paren):
        # focus on the first year, then deal with any others
        prev = pretext.split(' ')[-2]
        if prev.startswith('al'):  # Alpha et al. (YYYY)
            prevprev = pretext.split(' ')[-4]
            test_cite = ''.join([prevprev,'EA',paren[0][:4]])

            is_badref,is_abamb = _test_test_cite(test_cite,bibkeys)
            if not is_badref and not is_abamb:
                citations.append(test_cite + 'a')
                pretext = ' '.join(pretext.split(' ')[:-4]) + ' ' # remove authors from line

        else:  # Alpha (YYYY) or Alpha and Beta (YYYY)
            test_cite = ''.join([prev,paren[0][:4]])  # try just one name first
            is_badref,is_abamb = _test_test_cite(test_cite, bibkeys)
            if is_badref:
                prevprev = pretext.split(' ')[-4]  # skip backwards over expected "and"
                test_cite = ''.join([prevprev,prev,paren[0][:4]])
                is_badref,is_abamb = _test_test_cite(test_cite,bibkeys)
                if not is_badref and not is_abamb:
                    citations.append(test_cite + 'a')
                    pretext = ' '.join(pretext.split(' ')[:-4]) + ' '

        # if we couldn't parse this thing, return something to write to mark it
        if is_badref:
            parsed = '\\textcolor{red}{bad ref skipped: %s}' % ' '.join(paren)
            return parsed, pretext
        if is_abamb:
            parsed = '\\textcolor{red}{a/b ambiguity: %s}' % ' '.join(paren)
            return parsed, pretext

        if len(yr_inds) > 1:  # ie more than one year, same authors - Alpha et al. (2010, 2011)
            for i in range(1,len(yr_inds)):
                initial_cite = test_cite[:-4]
                test_cite = ''.join([initial_cite,paren[i][:4]])
                is_badref,is_abamb = _test_test_cite(test_cite,bibkeys)
                if is_badref:
                    parsed = '\\textcolor{red}{bad ref skipped: %s}' % ' '.join(paren) 
                    return parsed, pretext
                if is_abamb:
                    parsed = '\\textcolor{red}{a/b ambiguity: %s}' % ' '.join(paren)
                    return parsed, pretext 
                if not is_badref and not is_abamb:
                    citations.append(test_cite + 'a')

        # having read through all possible years in this year-only parenthetical, 
        # compile citation and return
        parsed = '\citet{'
        parsed += ', '.join(citations)  # add on citations and separators
        parsed += '}'  # remove trailing comma and space, close the bracket

        return parsed, pretext

    # CASE: not only years, so all citation info should be within the parens
    yr_inds = yr_inds + 1   # for easier looping/selecting the text bits
    yr_inds = np.append(0, yr_inds)

    # loop those year-index places
    for l in range(len(yr_inds) - 1):
        # choose bits corresponding to one particular year index
        bits = paren[yr_inds[l]:yr_inds[l+1]]
        # remove punctuation from these text pieces
        bits = [word.translate({ord(k): None for k in ['.',',','&','\\',';']}) \
                for word in bits]

        # check if this piece of the parenthetical is just a year (Alpha, 2010; 2011)
        if len(bits) == 1 and bits[0][:4].isdigit():
            # if we have a citation in the list already, try using that one
            if len(citations) == 0:  # nothing to work with here, not sure why
                badtext += 'bad ref: %s ' % bits[0]
            else:
                test_cite = citations[-1][:-5] + bits[0][:4]  # new citation to test
                is_badref,is_abamb = _test_test_cite(test_cite,bibkeys)
                if is_badref:
                    badtext += 'bad ref: %s ' % test_cite
                if is_abamb:
                    badtext += 'a/b: %s' % test_cite
                if not is_badref and not is_abamb:
                    citations.append(test_cite+'a')

        else:  # set of bits has more than just a year
            # replace et al. with EA, remove 'and' if present
            bits = _etal_and(bits)

            # make a test citation and see if it works
            test_cite = ''.join(bits)
            is_badref,is_abamb = _test_test_cite(test_cite,bibkeys)
            if is_abamb:
                badtext += 'a/b: %s ' % test_cite
            if is_badref and l == 0:
                for j in range(yr_inds[l]+1,yr_inds[l+1]):
                    bits = paren[j:yr_inds[l+1]]  # scrape off first word and try again
                    bits = [word.translate({ord(k): None for k in ['.',',','&','\\',';']}) \
                            for word in bits]
                    bits = _etal_and(bits)
                    test_cite = ''.join(bits)
                    is_badref,is_abamb = _test_test_cite(test_cite,bibkeys)
                    if not is_badref and is_abamb:
                        badtext += 'a/b AND preamble: %s ' % test_cite
                        break
                    if not is_badref and not is_abamb:
                        is_preamble = True
                        preamble_text = escape_latex(' '.join(paren[:j]))
                        break
                if is_badref: # we couldn't parse this one, even with scraping
                    bits = paren[yr_inds[l]:yr_inds[l+1]]
                    badtext += 'bad ref: %s' % ' '.join(bits)
            if is_badref and l != 0:  # can't read reference and it's not the first citation here
                badtext += 'bad ref: %s' % test_cite
            if not is_badref and not is_abamb:  # we parsed it! yay!
                citations.append(test_cite+'a')

    # combine citations into \citep, including preamble if there is one
    if len(citations) == 0:  # we failed to parse anything here :(
        parsed = '(' + ' '.join(paren) + ')'  # put it back in parentheses and hope its ok
    else:
        if is_preamble:
            parsed = '\citep[%s][]{' % preamble_text
        else:
            parsed = '\citep{'
        parsed += ', '.join(citations)
        parsed += '}'

        if len(badtext) != 0:
            parsed += ' \\textcolor{red}{NOTE %s}' % badtext

    return parsed, pretext


def _test_test_cite(test_cite,bibkeys):
    """
    take a citation tag and test it against bibkeys; return if no match or if a/b ambiguous
    """
    is_badref = False
    is_abamb = False

    if test_cite.lower() + 'a' not in bibkeys:
        is_badref = True
    else:
        if test_cite.lower() + 'b' in bibkeys:
            is_abamb = True

    return is_badref, is_abamb


def _etal_and(bits):
    """
    replace 'et al' with EA; remove 'and' from list of pieces
    """
    et_ind = [e == 'et' for e in bits]
    if sum(et_ind) > 0:
        et_ind = np.where(et_ind)[0][0]
        bits[et_ind] = 'E'
        bits[et_ind+1] = 'A'
    and_ind = [e == 'and' for e in bits]
    if sum(and_ind) > 0:
        and_ind = np.where(and_ind)[0][0]
        bits = np.delete(bits,and_ind)
    return bits

########################################################################
# tex escaping for python
########################################################################

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

