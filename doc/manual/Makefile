.PHONY : default clean

default :
	python3 dep.py < manual.tex > manual_expanded.tex
	latexmk -pdf -shell-escape "manual_expanded"
	mv manual_expanded.pdf manual.pdf

clean :
	latexmk -c
