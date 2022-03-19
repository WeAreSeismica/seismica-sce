import biblib.bib as bbl
import sce_utils.tex_templates as tt
import sce_utils.utils as ut
import numpy as np
import os, sys


########################################################################
# run through a pandoc'd latex file line by line, correcting things pandoc doesn't catch well
# in particular inline citations (so also read corresponding bibtex first)
# NOTE: this script assumes:
    # the input file used the seismica docx template, and used it *properly* (esp. headers/styles)
    # equations were typeset using word's native equation thing
    # there are no more than 99 equations, figures, and tables, respectively, in the document
    # a bibtex file using the reference list has already been created (see: anystyle, fix_bibtex.py)
    # references/bibliography is the LAST SECTION of the document, nothing after it will be kept
    # Table and Figure captions start with the capitalized words 'Table' or 'Figure'
# TODO:
    # parsing ORCIDS? If they are included in the word template??
    # editor name, dates rec/acc/pub, volume, issue, DOI for the article itself [maybe interactive]
        # OR at least print some message reminding people to change them
        # (there will have to be a checklist for a bunch of this stuff)
    # fast reports options?
########################################################################

########################################################################
# set filenames and review status  TODO: set these filenames to get started
bibtex = 'test_init.bib'
tex_in = 'test_pandoc.tex'
tex_mid = 'test_temp.tex'
tex_out = 'test_init.tex'
junk_out = 'junk.tex'  # this is for table and figure info that can't be parsed automatically
review = False  # switch for line numbers (and single-column format)

########################################################################
# set up files etc:
# read bibtex, get list of keys for entries that we expect to find in the text
parser = bbl.Parser()
biblio = parser.parse(open(bibtex,'r'))
bibkeys = biblio.get_entries().keys()

# open pandoc file and output file
ftex_in = open(tex_in,'r')
ftex_out = open(tex_mid,'w')
fjunk = open(junk_out,'w')

# set up counters for figures, equations, and tables
nfig = 1; nequ = 1; ntab = 1
figcap = {}; tabcap = {}

special_section_names = ['acknowledgements','acknowledgments','data-availability','author-contributions']  # for sections that aren't numbered, lowercase and with spaces as -
skip_sections = ['references','bibliography']  # when we get to this header, skip to the end

########################################################################
# start at the beginning, deal with title, authors, and abstracts
# skip header stuff from pandoc that seismica.cls will replace, find manuscript title
while True:
    line = ftex_in.readline()
    if line.startswith('\\begin{document}'):
        break

while True:
    line = ftex_in.readline()
    if line != '\n':
        break  # this should be the title, fingers crossed

# get the title text
article_title = line.rstrip()

# read in author info (names, affiliations, email for corresponding if applicable)
while True:  # read up to where authors start
    line = ftex_in.readline()
    if line != '\n':
        break  # author names, prior to affiliations
authors = {}  # read author names and superscripts for affiliations
for i,bit in enumerate(line.split('}')[:-1]):
    bit2 = bit.split('\\textsuperscript{')
    if bit2[0].startswith(','):
        nm = bit2[0][1:].lstrip()
        if nm.startswith('and'):
            nm = nm[3:].lstrip()
        elif nm.startswith('&'):
            nm = nm[1:].lstrip()
    else:
        nm = bit2[0]
    sp = bit2[1]
    authors[i] = {'name':nm,'supers':sp}

affils = {}  # read affiliations that go with those superscripts
while True:
    line = ftex_in.readline()
    if line.startswith('\\textsuperscript'):  # an affiliation
        bits = line.split('}')
        sp = bits[0].split('{')[1]
        pl = bits[1].rstrip()
        affils[int(sp)] = {'super':sp,'place':pl}
    elif line.startswith('*'):  # corresponding author email address
        email = line.split(':')[-1].lstrip()
        for k in authors.keys():
            if '*' in authors[k]['supers']:
                authors[k]['corresp'] = email.rstrip()
    elif line.startswith('\hypertarget') or line.startswith('\section'):  # hopefully not \section
        break  # stop at the first abstract

# read up to abstract heading
while True:
    line = ftex_in.readline()
    if line.startswith('\section{Abstract}'):
        break

# read lines cautiously, find the (first/English-language) abstract text
abst = ""
while True:
    line = ftex_in.readline()
    if not line.startswith('\hypertarget'):
        abst = abst + line.rstrip()
    else:
        break

other_langs = []
abs2 = None; abs2_dict = {}
# deal with the second-language abstract  if there is one
if line.startswith('\hypertarget{second-language-abstract'):
    ftex_in, line, abs2, abs2_dict = ut.get_abstract(ftex_in) # this function reads up to the
    other_langs.append(abs2_dict['language'])                 # next \hypertarget

abs3 = None; abs3_dict = {}
# deal with the third-language abstract  if there is one
if line.startswith('\hypertarget{third-language-abstract'):
    ftex_in, line, abs3, abs3_dict = ut.get_abstract(ftex_in)
    other_langs.append(abs3_dict['language'])

# feed some info to the header setup code
ftex_out = tt.set_up_header(ftex_out,article_title,authors=authors,affils=affils,review=review,\
            other_langs=other_langs)

# add abstract(s) after header
ftex_out = tt.add_abstract(ftex_out,abst,abs2=abs2,abs2_dict=abs2_dict,\
                            abs3=abs3,abs3_dict=abs3_dict)

########################################################################
# go through the rest of the sections! and deal with citations, figures, and equations

goto_end = False   # flag to stop reading/writing at references section
first_line = True  # abstract reading stopped at a section header, so don't read past that
while not goto_end:
    if not first_line:  # for when we already read the \hypertarget to get to the end of the abs.
        line = ftex_in.readline()
    else:
        first_line = False
    if line.startswith('\end{document}'): # this is the end, stop reading
        break  # shouldn't hit this unless there is no reference section

    if line.startswith('\hypertarget'):  # the next line will be a section heading
        lower_section = line.split('{')[1].split('}')[0]
        line = ftex_in.readline()  # actual section line
        stype = line.split('{')[0]
        if lower_section in special_section_names:
            sname = line.split('{')[1].split('}')[0]
            stype = stype + '*'
        elif lower_section in skip_sections:  # skip everything past "References"
            goto_end = True
        else:
            sname = ' '.join(line.split('{')[1].split('}')[0].split(' ')[1:])  # strip leading number
        if sname != '':
            ftex_out.write('%s{%s}\n' % (stype,sname))

    else:  # not a section header, so parse as a line and deal with citations or math or whatever
        if line.startswith('\('):  # possibly an equation
            print(line[:-1])
            iq = input('is this an equation? [y]/n') or 'y'
            if iq.lower() == 'y':
                # scrape off the \( and \) bits since we're putting this in an environment
                line = line.split('\)')[0].split('\(')[1]
                ftex_out.write('\\begin{equation}\n')
                ftex_out.write(line)
                ftex_out.write('\n')
                ftex_out.write('\label{eq%i}\n' % nequ)
                ftex_out.write('\end{equation}\n')
                nequ += 1
            else:
                print('ok, writing line plain, then')
                ftex_out.write(line)

        elif line.startswith('\\begin{'):  # some kind of environment?
            ftex_in, ftex_out, fjunk, nequ, nfig, ntab, itype = \
                    ut.parse_environment(line,ftex_in,ftex_out,fjunk,nequ,nfig,ntab)

        elif line.startswith('\includegraphics'):
            ftex_out.write('\\begin{figure}\n')
            ftex_out.write('\includegraphics[width = \columnwidth]{example-image}\n')
            ftex_out.write('\caption{placeholder caption}\n')
            ftex_out.write('\label{fig%i}\n' % nfig)
            ftex_out.write('\end{figure}\n')
            print('figure found; moving original line to junk file')
            fjunk.write('Figure %i\n' % nfig)
            fjunk.write(line)
            fjunk.write('\n')  # saving for later
            nfig += 1

        else:
            # parse the line for parenthetical citations etc (there are some TODO s in this function)
            to_write = ut.parse_parentheticals(line,bibkeys)

            # rescan line and look for figure/equation references to link
            to_write = ut.check_for_fig_tab_eqn_refs(to_write)

            # a few last checks for special cases:
            if to_write.startswith('Figure') or to_write.startswith('Table'): # likely a caption
                print('\t'+to_write[:40])
                iq = input('Is this a caption? [y]/n') or 'y'
                if iq.lower() == 'y':  # save in caption dict, don't write here
                    cap = to_write.split('\\ref{')[1]
                    tag = cap.split('}')[0]
                    if to_write.startswith('Figure'):
                        figcap[tag] = to_write.split(tag)[1][2:].lstrip()
                    elif to_write.startswith('Table'):
                        tabcap[tag] = to_write.split(tag)[1][2:].lstrip()
                    to_write = ''
            elif to_write[0].islower():           # lines (paragraphs) that start with lowercase
                ftex_out.write('\\noindent \n')   # are probably continuing sentences after eqns
            ftex_out.write(to_write)    # finally, write the line


ftex_out.write('\\bibliography{%s}\n' % bibtex.split('/')[-1].split('.')[0])
ftex_out.write('\end{document}')

ftex_in.close()
ftex_out.close()
fjunk.close()

# reread to put in figure captions
ftex_in = open(tex_mid,'r')  # open intermediate file
ftex_out = open(tex_out,'w')

while True:
    line = ftex_in.readline()
    if line.startswith('\\begin{figure}'):
        temp = [line]
        while True:
            line = ftex_in.readline()
            temp.append(line)
            if line.startswith('\label'):
                tag = line.split('\label{')[1].split('}')[0]
            if line.startswith('\end{'):
                break

        for t in temp:
            if t.startswith('\caption'):
                ftex_out.write('\caption{%s}\n' % figcap[tag])
            else:
                ftex_out.write(t)

    elif line.startswith('\\begin{table}'):
        temp = [line]
        while True:
            line = ftex_in.readline()
            temp.append(line)
            if line.startswith('\label'):
                tag = line.split('\label{')[1].split('}')[0]
            if line.startswith('\end{table}'):  # can't be \end{tabular}
                break

        for t in temp:
            if t.startswith('\caption'):
                ftex_out.write('\caption{%s}\n' % tabcap[tag])
            else:
                ftex_out.write(t)

    elif line.startswith('\end{document'):
        ftex_out.write(line)
        break
    else:
        ftex_out.write(line)
        
ftex_in.close()
ftex_out.close()
