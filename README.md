# SQUARES - A SQL Synthesizer Using Query Reverse Engineering

Given a set of input-output examples (tables), SQUARES returns the desired query in R and in SQL. SQUARES is built on top of [Trinity](https://github.com/fredfeng/Trinity). Therefore, the same packages are required.

- Prerequisite:
    - python 3.6+
    
How to use:

+ using  Jupyter Notebook:
    - Go to jupyter-notebook folder and launch the jupyter notebook and select demo.ipynb:
        ```
        jupyter notebook
        ```
  
+ using [Google Colab](https://colab.research.google.com/drive/1wPwP1iWBLqmNTk9ffxNPR0mj3GbbUZr2):
    - save the google colab doc to your account and run it.

+ using terminal:
```
python3 squaresEnumerator.py [tree|lines] [flags -h, ...] input.in
```

    -  Flags:
    + -h : help
    + -on : computing symmetries online
    + -off : computing symmetries offline
    + -nr : only SQL query
    + -d : debug info

    Default: lines enumerator and without symmetry breaking

    -- Input Files (.in): Some examples can be found in tests-examples folder

-- Files required to integrate SQUARES in Trinity:
 + tyrell/enumerator/lines.py
 + tyrell/enumerator/lattices
 + tyrell/enumerator/gen_lattices.py
 + squares-enumerator.py
 + setup.py (modified)


-- Python packages (install using pip or conda):
 + sqlparse
 + z3-solver
 + sexpdata
 + click
 + rpy2

-- R packages (install using conda or R console):
 + dplyr
 + dbplyr
 + tidyr
 + stringr

References

 + Pedro Orvalho, Miguel Terra-Neves, Miguel Ventura, Ruben Martins and Vasco Manquinho. Encodings for Enumeration-Based Program Synthesis. CP'19
 + Pedro Orvalho. SQUARES : A SQL Synthesizer Using Query Reverse Engineering. MSc Thesis. Instituto Superior Técnico - Universidade de Lisboa. 2019.
 - Yu Feng, Ruben Martins, Osbert Bastani, Isil Dillig. Program Synthesis using Conflict-Driven Learning. PLDI'18.
 - Yu Feng, Ruben Martins, Jacob Van Geffen, Isil Dillig, Swarat Chaudhuri. Component-based Synthesis of Table Consolidation and Transformation Tasks from Examples. PLDI'17
 - Yu Feng, Ruben Martins, Yuepeng Wang, Isil Dillig, Thomas W. Reps. Component-Based Synthesis for Complex APIs. POPL'17

