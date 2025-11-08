#!/bin/bash

echo "Switching working directory"

# cd to the directory where the script lies in
cd "$( dirname "${BASH_SOURCE[0]}" )"
pwd

echo "Starting benchmarking."
date
python3 ../scripts/run.py -t stationary -r results -f inv10.json

echo "Starting postprocessing of results "
python3 ../scripts/postprocess.py -t stationary -r results -l 10 --compare
cp results/plots/wallclock-time-INC-relative-error-max-norm-value-quantile.csv latex/stationary-quantile.csv
cp results/plots/wallclock-time-INC-relative-error-max-norm-value-texpgf-scatter.csv latex/stationary-scatter.csv
cp results/plots/relative-error-max-norm-value-texpgf-scatter.csv latex/stationary-reldiff.csv


echo "Generating LaTex file."
cd latex
pdflatex --interaction=nonstopmode --halt-on-error plots.tex
cd ..

echo "----------------------------------------------"
echo "Output files: "
realpath results/tables/wallclock-time.html 
realpath latex/plots.pdf
echo "----------------------------------------------"

echo "Finished benchmarking."
date
