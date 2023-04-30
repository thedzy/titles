#!/usr/bin/env python3

import title
import random
from pathlib import Path


def main():
    # Create a title object
    with title.Title(resolution=14, font_height=52) as titler:
        # Reuse the object while changing the invert
        titler.print('Hello!')

        titler.set_font_size(24)
        titler.set_characters('\\\/|-_')
        titler.print('World', algorithm='norm')

        titler.set_font_size(32)
        titler.set_characters('▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐▔▕▖▗▘▙▚▛▜▝▞▟■')
        random_font = random.choice(list(Path('/Library/Fonts').iterdir())).as_posix()
        titler.set_font(random_font)
        titler.print('The quick brown fox jumped over the lazy dog', invert=True)


if __name__ == '__main__':
    main()
