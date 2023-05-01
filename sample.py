#!/usr/bin/env python3

import argparse
from pathlib import Path
import struct
import title


def main():
    # Create a title object
    with title.Title(characters=options.characters, resolution=options.resolution, font_height=options.font_height) as titler:
        for font in options.font_dir.glob('**/*'):
            if font.is_file():
                with open(font, 'rb') as f:
                    header = f.read(4)
                    if header not in (b'', b'OTTO', b'\x00\x01\x00\x00'):
                        continue
                print(f'-- {font.as_posix().ljust(120, "-")}')
                titler.set_font(font.as_posix())
                try:
                    for algorithm in options.algorithms:
                        print(f'-- Algorithm {algorithm.ljust(110, "-")}')
                        titler.print(options.text, invert=False, algorithm=algorithm)
                    print(f'-- {"Inverted".ljust(110, "-")}')
                    titler.print(options.text, invert=True)

                except Exception as err:
                    print(f'Error, {err}')


if __name__ == '__main__':
    def directory(path):
        if not Path(path).is_dir():
            raise argparse.ArgumentTypeError(f'{path} is not a directory')
        return Path(path)


    parser = argparse.ArgumentParser(description='See fonts')

    # Text to render
    parser.add_argument('-t', '--text',
                        action='store', dest='text', default='The quick brown fox jumped over the lazy dog',
                        help='text to render')

    # Fon directory
    parser.add_argument('-f', '--font-dir', type=directory,
                        action='store', dest='font_dir', default=Path('/Library/Fonts'),
                        help='font used to write in\n'
                             'default: %(default)s')

    parser.add_argument('-fh', '--font-height', type=int,
                        action='store', dest='font_height', default=100,
                        help='font height. default: %(default)s')

    # Characters
    parser.add_argument('-c', '--chars', type=str,
                        action='store', dest='characters', default='▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐▔▕▖▗▘▙▚▛▜▝▞▟■',
                        help='specify character sets that the system will used to render the text')

    # Algorithm
    parser.add_argument('-a', '--algorithms', nargs='+', default=['abs'],
                        action='store', dest='algorithms', choices=['abs', 'norm', 'outline', 'low'],
                        help='algorithm to use. choices: %(choices)s\n')

    # Resolution
    parser.add_argument('-r', '--resolution', type=int, default=15,
                        action='store', dest='resolution',
                        help='resolution')

    # Debug
    parser.add_argument('--debug', default=False,
                        action='store_true', dest='debug',
                        help=argparse.SUPPRESS)

    options = parser.parse_args()

    main()
