.PHONY : always clean

manual.pdf : manual_expanded.tex anthology.bib always
	latexmk -lualatex "manual_expanded" -jobname=manual

manual_expanded.tex : manual.tex
	python3 dep.py < $< > $@

anthology.bib : anthology.bib.gz
	gunzip -k $<

clean :
	latexmk -c
	rm manual_expanded.tex
