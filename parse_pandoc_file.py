import biblib.bib as bbl
import sce_utils.tex_templates as tt
import sce_utils.utils as ut
import numpy as np
from argparse import ArgumentParser
import os, sys, re


########################################################################
# run through a pandoc'd latex file line by line, correcting things pandoc doesn't catch well
# in particular inline citations (so also read corresponding bibtex first)
# NOTE: this script assumes:
    # the input file used the seismica docx/odt template, and used it *properly* (esp. headers/styles)
    # equations were typeset using native equation thing
    # pandoc was run with the right options
    # there are no more than 99 equations, figures, and tables, respectively, in the document
    # a bibtex file using the reference list has already been created (see: anystyle, fix_bibtex.py)
    # references/bibliography is the LAST SECTION of the document, nothing after it will be kept
    # Table and Figure captions start with the capitalized words 'Table' or 'Figure'
# TODO:
    # finding ORCID and CRediT sections if not automatically ID'd
    # scan for URLs, wrap with \url{} for line breaking
########################################################################

########################################################################
# set filenames
########################################################################
parser = ArgumentParser()
parser.add_argument('--bibfile','-b',type=str,help='path to bibfile')
parser.add_argument('--ifile','-i',type=str,help='path to tex file from pandoc')
parser.add_argument('--ofile','-o',type=str,help='path to output tex file')
args = parser.parse_args()
bibtex = args.bibfile
if bibtex == None:
    bibtex = input('Enter path to bibfile: ') or 'refs_corr.bib'
assert os.path.isfile(bibtex),'bibfile does not exist'
tex_in = args.ifile
if tex_in == None:
    tex_in = input('Enter path to pandoc tex file: ') or 'test_pandoc.tex'
assert os.path.isfile(tex_in),'input tex file does not exist'
tex_out = args.ofile
if tex_out == None:
    of1 = tex_in[:-4] + '_corr.tex'
    tex_out = input('Enter path to output tex file, or use %s: ' % of1) or of1 
tex_mid = 'temp.tex'
junk_out = 'junk.tex'  # this is for table and figure info that can't be parsed automatically
review = False  # switch for line numbers (and single-column format) - always off for production

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

# for sections that aren't numbered, lowercase and with spaces as -
special_section_names = ['acknowledgements','acknowledgments',\
                        'data-availability','data-and-code-availability',\
                        'competing-interests']
skip_sections = ['references','bibliography']  # when we get to this header, skip to the end

########################################################################
# start by scraping overall structure
# and figuring out where the document itself starts
_,struct = ut.document_structure(ftex_in)

# determine which sections are ORCIDs and CRediT
orcid_key = -1; credit_key = -1; abs1_key = -1
for k in struct.keys():
    if struct[k]['sname'].lower().__contains__('orcid'):
        orcid_key = k
    if struct[k]['sname'].lower().__contains__('author contributions'):
        credit_key = k
    if struct[k]['sname'].lower() == 'abstract':  # specifically, the English-language one
        abs1_key = k

assert orcid_key >= 0, 'Author ORCIDs section not found'
assert credit_key >= 0, 'Author contributions section not found'
assert abs1_key >= 0, 'Abstract not found'

# deal with title and authors
# skip header stuff from pandoc that seismica.cls will replace, find manuscript title
ftex_in.seek(0)
for i in range(struct['b']['line']+1):
    line = ftex_in.readline()  # should read exactly to \begin{document}

# if title is in the document structure, we're done!
if 'ti' in struct.keys():
    article_title = struct['ti']['sname']
else:  # hopefully the title is the first line after begin{document}
    while True:
        line = ftex_in.readline()
        if line != '\n':
            break  # this should be the title, fingers crossed
    article_title = line.rstrip() # get the title text

# read in author info (names, affiliations, email for corresponding if applicable)
while True:  # read up to where authors start
    line = ftex_in.readline()
    if line != '\n' and not line.startswith(r'\maketitle'):
        break  # author names, prior to affiliations
authors = {}  # read author names and superscripts for affiliations
for i,bit in enumerate(line.split('}')[:-1]):
    bit2 = bit.split('\\textsuperscript{')
    nm = bit2[0].lstrip().rstrip()
    if nm.startswith(','):
        nm = nm[1:].lstrip().rstrip()
    if nm.startswith('&'):
        nm = nm[1:].lstrip()
    if nm.startswith('and'):
        nm = nm[3:].lstrip()
    sp = bit2[1]
    authors[i] = {'name':nm.lstrip().rstrip(),'supers':sp}

affils = {}  # read affiliations that go with those superscripts
while True:
    line = ftex_in.readline()
    if line.startswith('\\textsuperscript'):  # an affiliation
        bits = line.split('}')
        sp = bits[0].split('{')[1]
        pl = bits[1].rstrip()
        try:
            affils[int(sp)] = {'super':sp,'place':pl.lstrip().rstrip()}
        except ValueError:  # probably a superscript asterisk
            if sp == '*':
                email = line.split(':')[-1].lstrip()
                for k in authors.keys():
                    if '*' in authors[k]['supers']:
                        authors[k]['corresp'] = email.rstrip()
            else:  # maybe some other symbol eg for changing affiliation
                print('unknown afflitiation superscript; moving to junk')
                fjunk.write(line)
                fjunk.write('\n')
    elif line.startswith('*'):  # corresponding author email address
        email = line.split(':')[-1].lstrip()
        for k in authors.keys():
            if '*' in authors[k]['supers']:
                authors[k]['corresp'] = email.rstrip()
    elif line.startswith(r'\hypertarget') or line.startswith(r'\section'):  # hopefully not \section
        break  # stop at the start of a section

# remove asterisk from superscripts once email address is found (if * is superscripted)
for a in authors.keys():
    if '*' in authors[a]['supers']:  # need to remove extra * because \thanks takes care of that
        star_ind = authors[a]['supers'].find('*')
        if star_ind == len(authors[a]['supers'])-1:
            authors[a]['supers'] = authors[a]['supers'][:star_ind-1]
        else:
            pre = authors[a]['supers'][:star_ind]
            post = authors[a]['supers'][star_ind+2:]
            authors[a]['supers'] = pre+post

# parse orcids, add to author dict
ftex_in.seek(0)
for i in range(struct[orcid_key]['line']+1):
    line = ftex_in.readline()  # read up to ORCIDs section

while True:
    line = ftex_in.readline()
    if line != '\n':  # there is something to parse
        if line.startswith(r'\hypertarget') or line.startswith(r'\section'):
            break
        # figure out who the author is, locate in author dict
        orcid_claimed = False
        for k in authors.keys():
            if ut.author_aliases(line.split(':')[0],authors[k]['name']):
                authors[k]['orcid'] = line.split(':')[1].lstrip().rstrip()
                orcid_claimed = True
        if not orcid_claimed:
            print('orcid ',line.split(':'),' not matched to author list')

# parse CRediT section, make a dict for that
ftex_in.seek(0)
for i in range(struct[credit_key]['line']+1):
    line = ftex_in.readline()  # read up to CRediT section

credits = {}
while True:
    line = ftex_in.readline()
    if line != '\n':
        if line.startswith(r'\hypertarget') or line.startswith(r'\section'):
            break
        key = line.split(':')[0]
        vals = line.split(':')[1].lstrip().rstrip()
        credits[key] = vals

# go to the abstract and start reading that stuff
ftex_in.seek(0)
for i in range(struct[abs1_key]['line']+1):
    line = ftex_in.readline()

# read lines cautiously, find the (first/English-language) abstract text
summaries = {}; scount = 0
abst = ""
while True:
    line = ftex_in.readline()
    if not line.startswith(r'\hypertarget'):
        abst = abst + line.rstrip()  # this will probably be just one line(/one paragraph)
    else:                            # but there can be multi-paragraph abstracts
        break
summaries[scount] = {'text':abst,'name':'Abstract','language':'English'}
scount += 1

other_langs = []
# deal with the second-language abstract  if there is one
if line.startswith(r'\hypertarget{second-language-abstract'):
    ftex_in, line, abs2_dict = ut.get_abstract(ftex_in) # this function reads up to the
    other_langs.append(abs2_dict['language'])                 # next \hypertarget
    summaries[scount] = abs2_dict
    scount += 1

# deal with the third-language abstract  if there is one
if line.startswith(r'\hypertarget{third-language-abstract'):
    ftex_in, line, abs3_dict = ut.get_abstract(ftex_in)
    other_langs.append(abs3_dict['language'])
    summaries[scount] = abs3_dict
    scount += 1

print('here')
# parse (English-language) non-technical summary if present
if line.startswith(r'\hypertarget{non-technical-summary'):
    line = ftex_in.readline()  # get past \section
    nontech = ""
    while True:
        line = ftex_in.readline()
        if not line.startswith(r'\hypertarget'):
            nontech = nontech + line.rstrip()
        else:
            break
    summaries[scount] = {'text':nontech,'name':'Non-technical summary','language':'English'}
    scount += 1

# feed some info to the header setup code
ftex_out = tt.set_up_header(ftex_out,article_title,authors=authors,affils=affils,credits=credits,\
            other_langs=other_langs)

# add abstract(s) after header
ftex_out = tt.add_abstracts(ftex_out,summaries)

########################################################################
# go through the rest of the sections! and deal with citations, figures, and equations

goto_end = False   # flag to stop reading/writing at references section
first_line = True  # abstract reading stopped at a section header, so don't read past that
while not goto_end:
    if not first_line:  # for when we already read the \hypertarget to get to the end of the abs.
        line = ftex_in.readline()
    else:
        first_line = False
    if line.startswith(r'\end{document}'): # this is the end, stop reading
        break  # shouldn't hit this unless there is no reference section

    if line.startswith(r'\hypertarget'):  # the next line will be a section heading
        lower_section = line.split('{')[1].split('}')[0]
        line = ftex_in.readline()  # actual section line
        stype = line.split('{')[0]
        if lower_section in special_section_names:
            sname = line.split('{')[1].split('}')[0]
            stype = stype + '*'
        elif lower_section in skip_sections:  # skip everything past "References"
            goto_end = True
        else:
            # check if there *is* a leading number
            lead_num = ' '.join(line.split('{')[1].split('}')[0][0])
            if lead_num.isdigit():
                sname = ' '.join(line.split('{')[1].split('}')[0].split(' ')[1:])  # strip leading number
            else:
                sname = line.split('{')[1].split('}')[0]  # no number, just heading
        if sname != '' and not goto_end:
            ftex_out.write('%s{%s}\n' % (stype,sname))

    else:  # not a section header, so parse as a line and deal with citations or math or whatever
        if line.startswith(r'\(') or line.startswith(r'\['):  # possibly an equation
            print(line[:-1])
            iq = input('is this an equation? [y]/n: ') or 'y'
            sw = line[:2]
            if sw[1] == '(': ew = r'\)'
            if sw[1] == '[': ew = r'\]'
            if iq.lower() == 'y':
                # scrape off the \( and \) bits since we're putting this in an environment
                line = line.split(sw)[1].split(ew)[0]
                ftex_out.write(r'\begin{equation}')
                ftex_out.write('\n')
                ftex_out.write(line)
                ftex_out.write('\n')
                ftex_out.write(r'\label{eq%i}' % nequ)
                ftex_out.write('\n')
                ftex_out.write(r'\end{equation}')
                ftex_out.write('\n')
                nequ += 1
            else:
                print('ok, writing line plain, then')
                ftex_out.write(line)

        elif line.startswith('\\begin{'):  # some kind of environment?
            ftex_in, ftex_out, fjunk, nequ, nfig, ntab, itype = \
                    ut.parse_environment(line,ftex_in,ftex_out,fjunk,nequ,nfig,ntab)

        elif line.startswith(r'\includegraphics'):
            ftex_out.write(r'\begin{figure*}[ht!]')
            ftex_out.write('\n')
            ftex_out.write(r'\centering')
            ftex_out.write('\n')
            ftex_out.write(r'\includegraphics[width = \\textwidth]{figure%i}' % nfig)
            ftex_out.write('\n')
            ftex_out.write(r'\caption{\\textcolor{red}{placeholder caption}}')
            ftex_out.write('\n')
            ftex_out.write(r'\label{fig%i}' % nfig)
            ftex_out.write('\n')
            ftex_out.write(r'\end{figure*}')
            ftex_out.write('\n')
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

            # rescan line and look for urls that need wrapping
            to_write = ut.check_href_make_url(to_write)

            # rescan again to replace spaces for reference links with ~ (non-breaking)
            to_write = ut.non_breaking_space(to_write)

            # a few last checks for special cases:
            regex_figcap = bool(re.match(r'^Figure [1-9]{1,2}[\.:]',to_write))  # try to match lines that are promising but missing bold tag
            regex_tabcap = bool(re.match(r'^Table [1-9]{1,2}[\.:]',to_write))
            start_figcap = to_write.lstrip().startswith('\\textbf{Figure')
            start_tabcap = to_write.lstrip().startswith('\\textbf{Table')
            if start_figcap or start_tabcap or regex_figcap or regex_tabcap: # likely a caption
                print('\t'+to_write[:40])
                iq = input('Is this a caption? [y]/n: ') or 'y'
                if iq.lower() == 'y':  # save in caption dict, don't write here
                    cap = '\\ref{'.join(to_write.split('\\ref{')[1:]).rstrip()  # no trailing \n
                    tag = cap.split('}')[0]
                    if to_write.startswith('\\textbf{Figure') or to_write.startswith('\\textbf{Table'):
                        splits = to_write.split(tag)
                        test = splits[1][2:].lstrip()
                        if test.startswith('}'):
                            test = test[1:].lstrip()
                        if len(splits) > 2:
                            fullcap = tag.join(np.append(test,splits[2:]))
                        else:
                            fullcap = test
                        if start_figcap or regex_figcap:
                            figcap[tag] = fullcap.lstrip().rstrip()
                        elif start_tabcap or regex_tabcap:
                            tabcap[tag] = fullcap.lstrip().rstrip()
                    to_write = ''

            elif to_write[0].islower():           # lines (paragraphs) that start with lowercase
                ftex_out.write('\\noindent \n')   # are probably continuing sentences after eqns

            ftex_out.write(to_write)    # finally, write the line

print(line)


ftex_out.write(r'\bibliography{%s}' % bibtex.split('/')[-1].split('.')[0])
ftex_out.write('\n')
ftex_out.write(r'\end{document}')

ftex_in.close()
ftex_out.close()
fjunk.close()

# reread to put in figure captions
ftex_in = open(tex_mid,'r')  # open intermediate file
ftex_out = open(tex_out,'w')

beg_doc = False
while True:
    line = ftex_in.readline()
    if line.startswith(r'\begin{document}'): beg_doc = True
    if line.startswith(r'\begin{figure'):
        print(line)
        temp = [line]
        while True:
            line = ftex_in.readline()
            temp.append(line)
            if line.startswith(r'\label'):
                tag = line.split(r'\label{')[1].split('}')[0]
            if line.startswith(r'\end{'):
                break

        for t in temp:
            #print(figcap)
            if t.startswith(r'\caption') and tag in figcap:
                ftex_out.write(r'\caption{%s}' % figcap[tag])
                ftex_out.write('\n')
            else:
                ftex_out.write(t)

    elif line.startswith(r'\begin{table'):
        temp = [line]
        while True:
            line = ftex_in.readline()
            temp.append(line)
            if line.startswith(r'\label'):
                tag = line.split(r'\label{')[1].split('}')[0]
            if line.startswith(r'\end{table'):  # can't be \end{tabular}
                break

        for t in temp:
            if t.startswith(r'\caption') and tag in tabcap:
                ftex_out.write(r'\caption{%s}' % tabcap[tag])
                ftex_out.write('\n')
            else:
                ftex_out.write(t)

    elif line.startswith(r'\end{document'):
        print(line)
        ftex_out.write(line)
        break
    else:
        ftex_out.write(line)
        
ftex_in.close()
ftex_out.close()

ut.print_reminders(tex_out)
