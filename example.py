#!/usr/bin/env python3

import title
import platform

def main():
    # Create a title object
    titles = title.Title('Hello')

    # Reuse the object while changing the invert
    titles.print('World!', characters='World!', invert=True)


    system = platform.uname().system.lower()
    if 'darwin' in system:
        titles.print('Full width', characters='▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐▒▓▔▕▖▗▘▙▚▛▜▝▞▟ ', font_size=0,
                     font_path='/System/Library/Fonts/MarkerFelt.ttC')

    elif 'windows' in system:
        titles.print('Full width', characters='▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐▒▓▔▕▖▗▘▙▚▛▜▝▞▟ ', font_size=0,
                     font_path='C:/Windows/Fonts/Impact.ttf')

    # Set the default for all future prints
    titles.set_font_size(32)
    titles.set_characters('\/|-_')
    titles.print('Test')


if __name__ == '__main__':
    main()