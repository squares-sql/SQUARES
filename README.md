# Tyrell+: Next-generation Synthesizer for Data Science

Dev Environment Setup
=====================
- Prerequisite:
    - python 3.6+  
- It is preferable to have a dedicated virtualenv for this project:
```
    $ git clone <this repo>
    $ cd Tyrell
    $ mkdir venv
    $ python3 -m venv venv
    $ source venv/bin/activate
```
- Make an editable install with `pip`. This would automatically handles package dependencies. One of our dependency, `z3-solver`, takes a long time to build. Please be patient.
```
    $ pip install -e ".[dev]"
```
- Test whether the installation is successful
```
    $ parse-spec example/toy.tyrell
```
- Run all unit tests
```
    $ python -m unittest discover .
```
    
Morpheus prerequisite
=====================
- R 3.3+ （https://cran.r-project.org/bin/macosx/R-3.5.2.pkg）
    - dplyr: install.packages("dplyr")
    - tidyr: install.packages("tidyr")
    - devtools: install.packages("devtools")
- Install MorpheusData for PLDI17 (optional): devtools::install_github("fredfeng/MorpheusData")
- Load MorpheusData for PLDI17 in R (optional): library(MorpheusData)
