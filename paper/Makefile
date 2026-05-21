# arXiv categories:
#   primary:    stat.ME   (Statistics -- Methodology)
#   secondary:  cs.CY     (Computers and Society)
#   optional cross-lists: cs.AI, cs.LG

FIGS = figures/step_vs_sigmoid.pdf \
       figures/propriety_verification.pdf \
       figures/uncertainty_aware_ranking.pdf \
       figures/real_data_comparison.pdf

main.pdf: main.tex refs.bib sections/*.tex $(FIGS)
	pdflatex -interaction=nonstopmode main.tex
	bibtex main
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

figures: $(FIGS)

figures/step_vs_sigmoid.pdf figures/propriety_verification.pdf figures/uncertainty_aware_ranking.pdf:
	cd ../ && uv run python -m cramer_distance.figures

# Real-data figure depends on pre-computed CSVs in data/.
# To regenerate CSVs from scratch, you need views-datafactory access.
figures/real_data_comparison.pdf: data/real_data_scores.csv
	cd ../ && uv run python -m cramer_distance.figures

clean:
	rm -f main.aux main.log main.out main.toc main.bbl main.blg \
	      main.fls main.fdb_latexmk main.synctex.gz sections/*.aux

distclean: clean
	rm -f main.pdf

.PHONY: figures clean distclean
