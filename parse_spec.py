import click
import spec as S
import dsl as D
import random
import logger

logger = logger.get('tyrell')


# A simple example showing how to use the Builder API to create an AST
class RandomASTGenerator:
    _depth_limit: int
    _builder: D.Builder

    def __init__(self, spec: S.TyrellSpec, depth_limit: int):
        self._builder = D.Builder(spec)
        self._depth_limit = depth_limit

    def _do_generate(self, curr_type: S.Type, curr_depth: int, force_leaf: bool):
        logger.debug('Generating AST for type {} at depth {}...'.format(
            curr_type, curr_depth))

        # First, get all the relevant production rules for current type
        productions = self._builder.get_productions_with_lhs(curr_type)
        if force_leaf:
            productions = list(
                filter(lambda x: not x.is_function(), productions))
        if len(productions) == 0:
            raise RuntimeError('RandomASTGenerator ran out of productions to try for type {} at depth {}'.format(
                curr_type, curr_depth))

        # Pick a production rule uniformly at random
        prod = random.choice(productions)
        logger.debug('Picked production {}'.format(prod.id))
        if not prod.is_function():
            # make_node() will produce a leaf node
            return self._builder.make_node(prod)
        else:
            # Recursively expand the right-hand-side (generating children first)
            children = [self._generate(x, curr_depth + 1) for x in prod.rhs]
            # make_node() will produce an internal node
            return self._builder.make_node(prod, children)

    def _generate(self, curr_type: S.Type, curr_depth: int):
        return self._do_generate(curr_type, curr_depth,
                                 force_leaf=(curr_depth >= self._depth_limit - 1))

    def generate(self):
        return self._generate(self._builder.output, 0)


def generate_ast(spec: S.TyrellSpec, depth: int):
    ast = RandomASTGenerator(spec, depth).generate()
    logger.info('Generated AST:')
    logger.info('  {}'.format(ast))


def print_spec(spec: S.TyrellSpec):
    logger.info('Defined types:')
    for ty in spec.types():
        logger.info('  {!r}'.format(ty))

    logger.info('Defined productions:')
    for prod in spec.productions():
        logger.info('  {}'.format(prod))


@click.command()
@click.argument(
    'spec_file',
    type=click.Path(
        exists=True, dir_okay=False,
        readable=True, allow_dash=True)
)
@click.option('-g', '--gen-depth',
              type=click.INT,
              help='If this option is set, generate a random AST for the spec with the specified maximum depth'
              )
@click.option('-v', '--verbosity',
              type=click.Choice([
                  'DEBUG',
                  'INFO',
                  'WARNING',
                  'ERROR',
                  'CRITICAL'
              ]),
              help='Set the verbosity of the logger',
              default='INFO'
              )
def cli(spec_file, gen_depth, verbosity):
    '''
    Next-generation Synthesizer for Data Science
    '''
    logger.setLevel(verbosity)
    try:
        with open(spec_file, 'r') as f:
            spec_str = f.read()
        tyrell_spec = S.parse(spec_str)
        print_spec(tyrell_spec)
        if gen_depth is not None:
            generate_ast(tyrell_spec, gen_depth)
    except (S.ParseError, S.ParseTreeProcessingError) as e:
        logger.error('Spec parsing error: {}'.format(e))
