import click

@click.command()
@click.option("--input", default="./input", help="Input DICOM folder")
@click.option("--target", default="./target", help="Target DICOM folder")
def runner(input, target):
    pass

if __name__ == '__main__':
    runner()