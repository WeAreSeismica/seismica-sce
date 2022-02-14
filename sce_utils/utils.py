import numpy as np
from re import finditer
import os, sys

####
# functions for text processing of pandoc outputs
####

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
                            shift = len(word)+ + 2
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
            print(hdr)
            abs2_dict['language'] = hdr.split('(')[0].rstrip()
            abs2_dict['name'] = hdr.split('(')[-1].split(')')[0]
        else:
            if not line.startswith('\hypertarget'):  # until we hit the next section
                abs2 = abs2 + line.rstrip()
            else:
                break 

    return ftex_in, line, abs2, abs2_dict

def parse_parentheticals(line,bibkeys):
    """
    for a line of text, parse parentheticals for citations and replace with appropriate \cite calls
    """
    # this is a stupidly complicated function. Would be nice to simplify it if possible (TODO)
    # TODO for real: preamble parsing for citations (like e.g.)
    # TODO: multiple years for the same authors (ie case where we have YYYY, YYYY)
    to_write = ''  # append pieces as you check them
    if '(' in line:  # check for parentheticals
        # find indices of open/close parens
        open_par = [pos for pos, char in enumerate(line) if char == '(']
        clse_par = [pos for pos, char in enumerate(line) if char == ')']
        if len(open_par) != len(clse_par):
            print('mismatched parentheticals :(')
            print(line)
            sys.exit()

        for k in range(len(open_par)):  # loop parentheticals, see if they look like citations
            if k == 0:  # add text before this parenthetical to the output string
                to_write += line[:open_par[k]]
            else:
                to_write += line[clse_par[k-1]+1:open_par[k]]
            if to_write[-1] == '\\':  # check if this paren is actually a math paren
                to_write += line[open_par[k]:clse_par[k]+1]
                break
            paren = line[open_par[k]+1:clse_par[k]]  # text within parens
            # signs of citation: contains et al., starts with e.g., match to bibkey
            # try to skip preambles, find first year
            paren = paren.split(' ')

            cite_text = '\citep{'

            yr_inds = np.where([e[:4].isdigit() for e in paren])[0] + 1
            yr_inds = np.append(0,yr_inds)
            for l in range(len(yr_inds)-1):
                # combine each set of pieces into a string, try to find in bib keys
                cite_pieces = paren[yr_inds[l]:yr_inds[l+1]]
                cite_pieces = [word.translate({ord(k): None for k in ['.',',','&','\\',';']}) \
                                for word in cite_pieces]  # remove punctuation
                if len(cite_pieces) == 1 and cite_pieces[0][:4].isdigit():  # just a year -> citet
                    prev = to_write.split(' ')[-2]
                    if prev.startswith('al'):  # this was an et al!
                        prevprev = to_write.split(' ')[-4]
                        test_cite = ''.join([prevprev,'EA',cite_pieces[0][:4]])
                        if test_cite.lower() + 'a' not in bibkeys:  # sus
                            cite_text = '\\textcolor{red}{bad ref skipped: %s}' % test_cite
                        else:
                            if test_cite.lower() + 'b' in bibkeys:  # ambiguity
                                cite_text = '\citet[\\textcolor{red}{a/b ambiguity}]{%s' % test_cite
                            else:
                                cite_text = '\citet{%s' % test_cite
                    else:  # not an et al, 1-2 authors
                        test_cite = ''.join([prev,cite_pieces[0][:4]])
                        if test_cite.lower() + 'a' not in bibkeys:  # try moving back farther
                            prevprev = to_write.split(' ')[-4]  # skip expected 'and'
                            test_cite = ''.join([prevprev,prev,cite_pieces[0][:4]])
                            if test_cite.lower() + 'a' not in bibkeys:  # sus
                                cite_text = '\\textcolor{red}{bad ref skipped: %s}' % test_cite
                            else:
                                if test_cite.lower() + 'b' in bibkeys:  # ambiguity
                                    cite_text = '\citet[\\textcolor{red}{a/b ambiguity}]{%s' % test_cite
                                else:
                                    cite_text = '\citet{%s' % test_cite
                    break
                et_ind = [e == 'et' for e in cite_pieces]  # look for et al
                if sum(et_ind) > 0:  # if there is an et al, deal with it
                    et_ind = np.where(et_ind)[0][0]
                    cite_pieces[et_ind] = 'E'  # replace the et al with EA
                    cite_pieces[et_ind+1] = 'A'
                and_ind = [e == 'and' for e in cite_pieces]  # look for 'and'
                if sum(and_ind) > 0:
                    and_ind = np.where(and_ind)[0][0]
                    cite_pieces = np.delete(cite_pieces, and_ind)
                test_cite = ''.join(cite_pieces)
                # check if this citation matches any of the keys in the bibliography
                if test_cite.lower() + 'a' not in bibkeys:
                    # possibly a preamble? try skipping a character at a time until it matches
                    for m in range(5,len(test_cite)):
                        if test_cite[-m:].lower() + 'a' in bibkeys:
                            preamble = tt.escape_latex(test_cite[:-m])
                            test_cite = test_cite[-m:]
                            cite_text = '\\textcolor{red}{'+preamble+ '}' + cite_text
                            if l == 0:
                                cite_text = cite_text + test_cite + 'a' # first citation
                            else:
                                cite_text = cite_text + ', ' + test_cite + 'a'
                            break
                    else:
                        cite_text = '\\textcolor{red}{bad ref skipped}' + cite_text

                else:  # 'a' *was* in the keylist
                    if test_cite.lower() + 'b' in bibkeys:
                        cite_text = 'ref year ambiguity ' + cite_text
                    if l == 0:
                        cite_text = cite_text + test_cite + 'a' # first citation
                    else:
                        cite_text = cite_text + ', ' + test_cite + 'a'
            cite_text = cite_text + '}'

            if cite_text.endswith('\citep{}'):  # parenthetical didn't match anything, keep it
                to_write += '(' 
                to_write += ' '.join(paren) 
                to_write += ')'
            else:
                to_write += cite_text

        if k == len(open_par) - 1:
            to_write += line[clse_par[-1]+1:]
    else:  # no parentheticals at all!
        to_write = line
    return to_write
