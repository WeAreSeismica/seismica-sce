# docx/odt parsing for Seismica

These scripts are for converting docx/odt manuscript submissions into latex, specifically a tex file that will work with the Seismica latex submission template. The scripts are a bit janky and not completely tested, so if anything breaks or doesn't work, it's probably my fault, not yours.

## dependencies:
- python 3.n (preferably 3.8+)
- numpy
- [biblib](https://github.com/WeAreSeismica/biblib) (NOT from conda or pip)
- [pandoc](https://pandoc.org/)
- [anystyle](https://github.com/inukshuk/anystyle) or a web browser to access [anystyle.io](anystyle.io)

A [conda](conda.io) environment is a nice way to set up the python dependencies. You could, for example, use these commands:

- `conda create -n seismica numpy`
- `cd /path/to/put/biblib/files`
- `git clone git@github.com:WeAreSeismica/biblib.git`
- `conda activate seismica`
- `pip install /path/to/put/biblib/files/biblib`

Note that biblib is not available through conda or pip (the one available from pip is not the same module), though it can be installed in a conda env by using pip with the downloaded source code. We use a fork of the original source code that has been updated for compatibility with Python 3.10+.

To install anystyle locally on a linux machine, run:
- `sudo apt install ruby-dev`
- `sudo gem install anystyle-cli`
Note that you will also need to have `make` installed on your system for this to work.

Alternatively, you can use [docker](docker.com), with instructions provided below.

### docker setup
1. [Install](docker.com/products/docker-desktop) and start the docker client on your computer.
1. From the repository directory, run the following commands in your terminal - 
    ```
    docker-compose run --build -it docx-converter
    ```
1. This will open a terminal session with all the necessary dependencies already installed. You can follow the remaining intructions in this terminal.
1. After completing the conversions, `exit` this terminal session and run the following to turn down the docker service - 
    ```
    docker-compose down
    ```
## general steps for the conversion process

1. Check the docx/odt file before running pandoc to ensure that template formatting is generally intact. If you run into trouble later, incorrect template formatting is probably at least part of the reason. There are some common errors we encounter; a checklist for avoiding them is below:
    - 2nd and 3rd language abstract headers must be in the format "Second language abstract: Resumen (Spanish)" 
    - headers must use header styles
    - authors must be listed on one line and affiliations are right after authors, one affiliation per line
    - references or bibliography must be the last section of the document
    - author contributions are given as CRediT statements at the beginning, and there is no separate Author Contributions Statement elsewhere
    - captions must be below the figures and tables they pertain to, and (for now) the words "Figure N" or "Table N" at the start of the caption must be in bold to be parsed properly.

1. convert article file to latex
    - docx: `pandoc file.docx -f docx -t latex --wrap=none -s -o file_pandoc.tex`
    - odt: `pandoc file.odt -f odt -t latex --wrap=none -s -o file_pandoc.tex`

1. convert text bibliography into a .bib file by either:
    - running the anystyle gem locally: copy the text of the references into a plain text file (e.g. `refs.txt`) with one reference per line, and then run `anystyle -f bib parse refs.txt .` to generate the file `refs.bib` (filename will be the same as the input, with suffix replaced by .bib)
    - copy-pasting bibliography from docx/odt into anystyle.io, and copy-pasting the output into a new .bib file

1. fix anystyle bibtex file year fields and keys, make a new .bib file
    - `python3 -m fix_bibtex --ifile refs.bib --ofile refs_better.bib`

1. parse the pandoc output tex file to a better tex format
    - `python3 -m parse_pandoc_file --bibfile refs_better.bib --ifile file_pandoc.tex --ofile file_better.tex`
    - unparsed tables and other confusing text will go in `junk.tex`
    - `temp.tex` is used for intermediate stages of parsing

1. make pdf by either:
    - compiling all the `_better` files in overleaf with the publication template (recommended), OR:
    - run bibtex and lualatex locally
        - `lualatex file_better.tex` -> `file_better.pdf`
        - `bibtex file_better.aux`
        - `lualatex file_better.tex`
        - `lualatex file_better.tex`
            - running at least twice gives inline references a chance to sort themselves out
    - The Seismica publication template is not publicly available. If you are testing out these scripts without it, try using the [Seismica submission template](https://github.com/WeAreSeismica/submission-template) (and pdflatex) instead. You will need to comment out some metadata macros in the document preamble - they will throw errors in the submission template.

1. complete other tasks to fix the latex files:
    - manually set options (breakmath, languages, report, etc) as necessary
    - manually link figure files (that the author uploaded separately) at the right sizes (1- or 2-column)
    - manually adjust for any citations that we couldn't parse (most should be marked in red, but some may have been missed altogether)
    - add extra hyphenation rules for words latex doesn't know if columns are overfull
    - manually wrap any urls in the text that weren't caught with \url{}
    - look at junk file and manually reformat/place tables in text where they belong

## TODO: 
- multi-line equations in brackets/parens! These are a problem, they break the paren parsing.
- print warning for references that start with special characters
- figure out longtable/table parsing to seistable so we don't need to move things to junk
- check for excess . at the beginnings of captions when bold formatting isn't perfect, and strip trailing newlines from captions (for tex2jats)
- can we catch captions even when "Figure 1"/"Table 1" is *not* bold? They should be bold but are not always
- check YYYYa/YYYYb citations
