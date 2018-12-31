import click
import spec as S
import logger

logger = logger.get('tyrell')


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
def cli(spec_file, verbosity):
    '''
    Next-generation Synthesizer for Data Science
    '''
    logger.setLevel(verbosity)
    try:
        with open(spec_file, 'r') as f:
            spec_str = f.read()
        tyrell_spec = S.parse(spec_str)
        print_spec(tyrell_spec)
    except (S.ParseError, S.ParseTreeProcessingError) as e:
        logger.error('Spec parsing error: {}'.format(e))
