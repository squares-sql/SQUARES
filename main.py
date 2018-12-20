import click
import toml


@click.command()
@click.argument(
    'spec_file',
    type=click.File('r'))
def cli(spec_file):
    '''
    Next-generation Synthesizer for Data Science
    '''
    try:
        toml_input = toml.load(spec_file)
        click.echo('Parsed TOML: {}'.format(toml_input))
    except toml.TomlDecodeError as e:
        click.echo('TOML decoding error: {}'.format(e), err=True)
