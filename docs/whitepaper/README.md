# Whitepaper

`centinel-engine-whitepaper-v1.tex` is the source.

The PDF is not in the repository. It was not rebuilt in the environment that
edited the source, so a stale binary is not shipped. The maintainer builds it
locally:

```bash
pdflatex -output-directory=docs/whitepaper docs/whitepaper/centinel-engine-whitepaper-v1.tex
```

Run it twice if the references need it. Do not commit the PDF until
`pdftotext` of that file matches the `.tex`.
