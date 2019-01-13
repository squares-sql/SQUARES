=================
Basic Synthesizer
=================

In :doc:`the previous tutorial <01_language>`, we managed to tell Tyrell *what* to synthesize. In this tutorial, we start to tackle the question of *how* to do the synthesis.


Synthesizer components
======================

In Tyrell's view, program synthesis is essentially a search problem. A synthesizer consists of a *enumerator*, which defines the search domain, and a *decider*, which defines the search success metric. To search for the desired program, the basic workflow is rather straightforward: we use the enumerator to enumerate all kinds of programs we may be interested in, and for each of them we invoke the decider to see if we have found the program we want. In pseudocode, the search process would be:

.. code-block:: python
  
  def synthesize(enumerator, decider):
      for prog in enumerator.enumerate():
          if decider.is_success(prog):
              return prog
      return None

The entire Tyrell framework is virtually built around a loop like this, except that the class and method names may not be an exact match. Of course, there are many optimization opportunities over this naïve search scheme. But the basic idea that synthesis is done via repeated interaction between an enumerator and a decider stays the same. 


The enumerator
==============

In Tyrell, :class:`~tyrell.enumerator.enumerator.Enumerator` is the abstract base class of all enumerators. It exposes :meth:`~tyrell.enumerator.enumerator.Enumerator.next`, which is expected to enumerate the next program (represented by :class:`~tyrell.dsl.node.Node`) in the entire search space, or ``None`` if the space has been exhausted. 

Below is a simple function that takes an enumerator, and prints out all programs that it enumerates:

.. code-block:: python

  def print_enumerations(enumerator):
      prog = enumerator.next()
      while prog is not None:
          print(prog)
          prog = enumerator.next()

To define a custom enumerator, inherit from :class:`~tyrell.enumerator.enumerator.Enumerator` and override the :meth:`~tyrell.enumerator.enumerator.Enumerator.next` method:

.. code-block:: python

  from tyrell.enumerator import Enumerator
  class MyEnumerator(Enumerator):
      # We need to define a dummy constructor here, as Enumerator's constructor is declared as abstract.
      def __init__(self):
          pass

      def next(self):
          return None

  print_enumerations(MyEnumerator())  # Prints nothing

In the previous example, nothing gets printed as the enumerator returns ``None`` directly. Storing more states inside ``MyEnumerator`` would make the search space non-empty (Please refer to :ref:`the previous tutorial <sec-syntax-spec>` for what is in the ``bin_arith.tyrell`` file):

.. code-block:: python

  from tyrell.spec import parse_file
  from tyrell.dsl import Builder
  from tyrell.enumerator import Enumerator

  # A enumerator that enumerate only one program
  class MyEnumerator(Enumerator):
      def __init__(self, prog):
          self._prog = prog
          self._done = False

      def next(self):
          if self._done:
              return None
          else:
              self._done = True
              return self._prog

  spec = parse_file('bin_arith.tyrell')
  enumerator = MyEnumerator(Builder(spec).from_sexp_string('(plus (@param 1) (const (IntConst 2)))'))
  print_enumerations(enumerator)  # Prints "plus(@param1, const(2))"

.. note::

  The two enumerator examples shown above are used to demonstrate how the :class:`~tyrell.enumerator.enumerator.Enumerator` interface works. Simple enumerators like these can be more easily constructed via :func:`~tyrell.enumerator.from_iterator.make_empty_enumerator`, :func:`~tyrell.enumerator.from_iterator.make_singleton_enumerator`, and :func:`~tyrell.enumerator.from_iterator.make_list_enumerator`.

More sophisticated enumerators usually need to take into account what the spec file look like. For example, if we want to exhaustively enumerate all programs defined by a given spec, we could use :class:`~tyrell.enumerator.exhaustive.ExhaustiveEnumerator`:

.. code-block:: python

  from tyrell.spec import parse_file
  from tyrell.enumerator import ExhaustiveEnumerator

  spec = parse_file('bin_arith.tyrell')
  enumerator = ExhaustiveEnumerator(spec, max_depth=3)  # The enumerator will never enumerates AST whose depth is greater than 3
  print_enumerations(enumerator)  # 872 programs will be printed out


Example-based decider
=====================

Among all the programs that an enumerator provides to us, the decider's job is to see which ones of them are desirable. In Tyrell, the abstract base class for decider is called :class:`~tyrell.synthesizer.synthesizer.Synthesizer` [#naming]_. Its :meth:`~tyrell.synthesizer.synthesizer.Synthesizer.analyze` method should be overriden if you want to define your own decider. Given a program (represented by :class:`~tyrell.dsl.node.Node`), if we want to accept it we need to let our ``analyze`` method returns :func:`~tyrell.synthesizer.result.ok`. Otherwise we return :func:`~tyrell.synthesizer.result.bad`:

.. code-block:: python

  from tyrell.spec import parse_file
  from tyrell.dsl import Builder
  from tyrell.synthesizer import Synthesizer, ok, bad

  # Define a synthesizer that accepts a specific program
  class MySynthesizer(Synthesizer):
      def __init__(self, prog):
          self._prog = prog

      def analyze(self, prog):
          if prog is self._prog:
              return ok()
          else:
              return bad()

  builder = Builder(parse_file('bin_arith.tyrell'))
  prog0 = builder.from_sexp_string('(plus (@param 1) (const (IntConst 2)))')
  prog1 = builder.from_sexp_string('(plus (@param 0) (const (IntConst 1)))')
  synthesizer = MySynthesizer(prog0)
  res0 = synthesizer.analyze(prog0)
  print(res0.is_ok())  # Print 'True'
  res1 = synthesizer.analyze(prog1)
  print(res1.is_ok())  # Print 'False'

.. rubric:: Footnotes

.. [#naming] We did not name this class ``Decider`` since it combines the functionality of both the decider and the synthesizer. 