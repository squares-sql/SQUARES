==============
Defining a DSL
==============

Tyrell is a framework that helps people build program *synthesizers*.

A synthesizer, as the name suggests, generates *programs* as its output. Therefore the first question to ask when building a synthesizer is: what do these programs looks like?

Shape of a program
==================

The Tyrell framework recognizes programs in a simplistic form: a program is an experession that can either be an atom or a function application:

::

  program := expr
  expr    := atom
           | func (expr*)

Here ``func`` just represents a function identifier. 

An atom is either a constant, or a reference to the program's input value:

::

  atom := const
        | "@param" INT

Here ``const`` represent a constant identifier, and `INT` is just an index of the corresponding input value.

For example, this is a valid program supported by Tyrell:

::

  mult(plus(@param0, 1), minus(@param1, 2))

Intuitively, this program tries to compute `f(x, y) = (x + 1) * (y - 2)`. 


Syntax specification
====================

Different domains may need different collections of functions and constants. Different functions may have different arities. It is also rarely the case that function arguments can take arbitrary values: Sometimes we know that certain argument may only be chosen from a small set of constants, and sometimes we know that certain argument may only be of a specific type. 

To help narrow down the space of valid programs, Tyrell uses *spec file* to refine a program's specification on a syntax level. Here is a simple example of such a spec file:

.. code-block:: none
  :linenos:

  enum IntConst {
    "0", "1", "2"
  }
  value IntValue;

  program BinaryArithFunc(IntValue, IntValue) -> IntValue;

  func const: IntValue -> IntConst;
  func plus: IntValue -> IntValue, IntValue;
  func minus: IntValue -> IntValue, IntValue;
  func mult: IntValue -> IntValue, IntValue;

Each spec file starts with type definitions (line 1 to 4). Tyrell supports two kinds of types:

- The ``enum`` type represent a type whose universe is a pre-defined set. In this example, arguments of the `IntConst` type may only be ``"0"``, ``"1"``, or ``"2"``. Note that elements in the set must be quoted.
- The ``value`` type represent a type whose universe cannot be pre-determined. This should be the case for the input/output of the program.

Next section in the spec file is the input/output definition (line 6). It starts with the keyword ``program``, followed by the name of the program, followed by the input types of the program, and finally the ``->`` symbol and the output type of the program. Note that the types that appear in this part of the spec file must all be ``value`` types.

In the end (line 8 to 11), we specify what functions may appear in the program, and what kind of arguments these function takes. Note that unlike the input/output definition, the return type of the function comes before all the argument types. In this example, we defined 4 functions: one unary function ``const`` that takes a ``IntConst`` and produces a ``IntValue``, and three binary functions ``plus``, ``minus``, and ``mult`` that take two ``IntValue`` and returns ``IntValue``.


Spec file parsing
=================

Tyrell comes with a pre-installed console script ``parse-tyrell-spec`` that can read the spec file and check its consistency. We can save our example as a file ``example.tyrell``, and feed it into the script:

.. code-block:: bash

  $ parse-tyrell-spec example.tyrell

If the spec file is correctly written, no error would be reported.

Alternatively, the spec parser can be directly accessed from a python script:

.. code-block:: python
  
  from tyrell.spec import parse_file
  spec = parse_file('example.tyrell')


Manual program construction
===========================

With the parsed ``spec``, one thing we can do is to quickly construct a program that conforms to this spec. This is available through :class:`~tyrell.dsl.builder.Builder` APIs.

.. code-block:: python

  from tyrell.spec import parse_file
  from tyrell.dsl import Builder
  spec = parse_file('example.tyrell')
  builder = Builder(spec)

  # Below we construct the program f(x, y) = (x + 1) * (y - 2)
  param_0 = builder.make_param(0)  # Use make_param to create input reference
  param_1 = builder.make_param(1)
  enum_1 = builder.make_enum('IntConst', '1')  # Use make_enum to create node of IntConst type
  enum_2 = builder.make_enum('IntConst', '2')
  const_1 = builder.make_apply('const', [enum_1])  # Use make_apply to create function application
  const_2 = builder.make_apply('const', [enum_2])  # Note that we need to wrap the enums into a 'const' node: otherwise the program will not type-check according to our spec
  plus_node = builder.make_apply('plus', [param_0, const_1])
  minus_node = builder.make_apply('minus', [param_1, const_2])
  prog = builder.make_apply('mult', [plus_node, minus_node])

  # Pretty-print the program
  print(prog)

The process can be simplified using :meth:`~tyrell.dsl.builder.Builder.from_sexp_string`:

.. code-block:: python

  # Program can be specified using S-expressions
  prog = builder.from_sexp_string(
      '''
      (mult
          (plus
              (@param 0)
              (const (IntConst "1"))
          )
          (minus
              (@param 1)
              (const (IntConst "2"))
          )
      )
      '''
  )
  print(prog)

  # Dump the program back into sexp form
  from sexpdata import dumps
  print(dumps(prog.to_sexp()))


Semantics specification
=======================

  .. todo:: Work in progress