# docx/odt parsing for Seismica

These scripts are for converting docx/odt manuscript submissions into latex, specifically a tex file that will work with the Seismica latex submission template. The scripts are a bit janky and not completely tested, so if anything breaks or doesn't work, it's probably my fault, not yours.

## dependencies:
- python 3.n (preferably 3.8+)
- numpy
- [biblib](https://github.com/aclements/biblib)

A [conda](conda.io) environment is a nice way to set this up. Alternatively, you can use [docker](docker.com), with instructions provided below.

### manual setup
You will also need to have [pandoc](pandoc.org/) installed for the initial conversion of the .docx file.

A local installation of the anystyle gem is recommended but not required as long as the web-hosted [anystyle.io](anystyle.io) exists. On a linux machine, this can be obtained by running: `sudo apt install ruby-dev` followed by `sudo gem install anystyle-cli`

Note that biblib is not available through conda or pip (the one available from pip is not the same module), though it can be installed in a conda env by using pip with the downloaded source code. A future version of these scripts may build in relevant parts of biblib since it's under an MIT license and that would remove the dependency on one person's github-hosted project.

Compiling the output tex file from this set of scripts into a pdf requires the Seismica publication tex template, which is not publicly available. However, it should be able to compile with the Seismica submission tex template if you comment out a few of the macros at the top of the output tex file.

### docker setup
1. [Install](docker.com/products/docker-desktop) and start the docker client on your computer.
1. From the repository directory, run the following commands in your terminal - 
    ```
    docker-compose run --build -it docx-converter
    ```
1. This will open a terminal session with all the necessary dependencies already installed. You can follow the remaining intructions in this terminal.
1. After completing te conversions, `exit` this terminal session and run the following to turn down the docker service - 
    ```
    docker-compose down
    ```


## general steps for the conversion process

- check a few things in the docx/odt file before running pandoc:
    - 2nd and 3rd language abstract headers in the format "Second language abstract: Resumen (Spanish)" 
    - title is the first line of the document
    - headers are using header styles
    - authors are all on one line and affiliations are right after authors, one affiliation per line
    - references or bibliography is the last section of the document
    - author contributions are given as CRediT statements at the beginning, and there is no separate Author Contributions Statement elsewhere
    - captions must be below the figures and tables they pertain to
    - template formatting is generally intact (if you run into trouble later, this is probably the reason)

1. convert article file to latex
    - docx: `pandoc file.docx -f docx -t latex --wrap=none -s -o file_pandoc.tex`
    - odt: `pandoc file.odt -f odt -t latex --wrap=none -s -o file_pandoc.tex`

1. convert text bibliography into a .bib file by either:
    - running the anystyle gem locally: copy the text of the references into a plain text file (e.g. `refs.txt`) with one reference per line, and then run `anystyle -f bib parse refs.txt .` to generate the file `refs.bib` (filename will be the same as the input, with suffix replaced by .bib)
    - copy-pasting bibliography from docx/odt into anystyle.io, and copy-pasting the output into a new .bib file

1. fix anystyle bibtex file year fields and keys, make a new .bib file
    - `python3 -m fix_bibtex --ifile refs.bib --ofile refs_better.bib`
        - filenames can be whatever you want; ofile is optional, or the script can set it for you
    - any non-ascii keys will be printed to stdout with option to correct while running script

1. parse the pandoc output tex file to a better tex format
    - `python3 -m parse_pandoc_file --bibfile refs.bib --ifile file_pandoc.tex --ofile file_pandoc_better.tex`
    - unparsed tables etc will go in `junk.tex`
    - `temp.tex` is used for intermediate stages of parsing

1. make pdf by either:
    - compiling all the `_better` files in overleaf with the publication template (recommended), OR:
    - run bibtex and lualatex locally
        - `lualatex tex_out.tex` -> `tex_out.pdf`
        - `bibtex tex_out.aux`
        - `lualatex tex_out.tex`
        - `lualatex tex_out.tex`
            - running at least twice gives inline references a chance to sort themselves out

1. complete other tasks to fix the latex files - 
    - manually set options (breakmath, languages, etc) as necessary
    - manually link figure files at the right sizes, adjust placement of automated \includegraphics as needed
        - pandoc does not extract image files from word so they will need to be uploaded separately
    - manually adjust for any citations and non-ascii characters that we couldn't parse (should be in red)
    - add extra hyphenation rules for words latex doesn't know if columns are overfull
    - manually wrap any urls in the text that pandoc didn't catch with \url{}
    - look at junk file and manually reformat/place tables in text where they belong

## TODO: 
- multi-line equations in brackets/parens! These are a problem, they break the paren parsing.
- print warning for references that start with special characters
- figure out longtable/table parsing to seistable so we don't need to move things to junk
- check for excess . at the beginnings of captions when bold formatting isn't perfect, and strip trailing newlines from captions (for tex2jats)
- can we catch captions even when "Figure 1"/"Table 1" is *not* bold? They should be bold but are not always
- check YYYYa/YYYYb citations
- make a docker instance so it's easier for people to run this whole thing
- (incorporate relevant parts of biblib)
