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
        tyrell_spec = spec.parse(spec_str)
        for ty in tyrell_spec.types():
            logger.info(repr(ty))
        for prod in tyrell_spec.productions():
            logger.info(str(prod))
    except (spec.ParseError, spec.ParseTreeProcessingError) as e:
        logger.error('Spec parsing error: {}'.format(e))
