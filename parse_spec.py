import click
import logger
import spec

logger = logger.get('tyrell')


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
        ast = spec.parse(spec_str)
        logger.info('{}'.format(ast.pretty()))
    except spec.ParseError as e:
        logger.error('Spec parsing error: {}'.format(e))
