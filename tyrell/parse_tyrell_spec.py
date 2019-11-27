from typing import cast
import click
import tyrell.spec as S
from tyrell.logger import get_logger

logger = get_logger('tyrell')


def print_spec(spec: S.TyrellSpec):
    if spec.num_types() > 0:
        logger.info('Defined types:')
        for ty in spec.types():
            logger.info('  {!r}'.format(ty))

    if spec.num_productions() > 0:
        logger.info('Defined productions:')
        for prod in spec.productions():
            logger.info('  {}'.format(prod))
            if prod.is_function():
                fprod = cast(S.FunctionProduction, prod)
                for expr in fprod.constraints:
                    logger.info('    Constraint: {}'.format(expr))

    if spec.num_predicates() > 0:
        logger.info('Defined predicates:')
        for pred in spec.predicates():
            logger.info('  {}'.format(pred))


@click.command()
@click.argument(
    'spec_file',
    type=click.Path(
        exists=True, dir_okay=False,
        readable=True, allow_dash=True)
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
              default='INFO')
def cli(spec_file, verbosity):
    '''
    Parse the given Tyrell DSL spec file
    '''
    logger.setLevel(verbosity)
    try:
        tyrell_spec = S.parse_file(spec_file)
        print_spec(tyrell_spec)
    except (S.ParseError, S.ParseTreeProcessingError) as e:
        logger.error('Spec parsing error: {}'.format(e))


if __name__ == '__main__':
    cli()
