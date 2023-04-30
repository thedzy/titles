#!/usr/bin/env python3

"""
Script:	title_creator.py
Date:	2020-05-04

Platform: MacOS/Windows/Linux

Description:
Convert an text to title
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Developer'

import argparse
import os
import platform

from PIL import Image, ImageFont, ImageDraw, ImageStat


def main():
    # Load font to be used
    font = ImageFont.truetype(options.font_brightness.name, 18)
    options.font.close()

    # Create shader
    if options.characters is not None:
        # Filter out duplicates
        characters = list(set(options.characters))
        characters.append(' ')

        # Get average brightness of a character
        character_values = {}
        for character in characters:
            character_image = Image.new('L', (10, 20), 0)
            draw = ImageDraw.Draw(character_image)
            draw.text((0, 0), character, font=font, fill=255, align='center')
            image_mean = ImageStat.Stat(character_image).mean[0]
            character_values[character] = image_mean

        # Sort the values into an array
        shader = []
        while len(character_values) > 0:
            key = min(character_values, key=character_values.get)
            shader.append(key)
            del character_values[key]
    else:
        shader = list(options.shader)
    shader_length = len(shader) - 1

    # Invert if black on white
    if options.black_on_white:
        shader = shader[::-1]

    # Get dimension but skip entirely if using custom settings
    window_width, window_height = os.get_terminal_size()

    # Load image
    font = ImageFont.truetype(options.font.name, options.font_height)
    options.font.close()

    image = Image.new('L', (window_width, int(options.font_height * 1.1)), 0)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), options.text, font=font, fill=255, align='center')

    # Calculate new sizes
    new_height = int(options.font_height / options.aspect)
    new_width = window_width

    # Resize image
    image = image.resize((new_width, new_height))

    # Get pixel data in RGB
    image_data = image.getdata()

    # Break image into a matrix of perceived values
    image_matrix = []
    for x in range(new_width):
        row = []
        for y in range(new_height):
            image_pixel = image_data.getpixel((x, y))
            image_contrast = int((image_pixel/255) * shader_length)
            row.append(image_contrast)
        image_matrix.append(row)

    # Write data out
    if options.border is not None:
        print(options.border[0] * window_width)
    for y in range(new_height):
        for x in range(new_width):
            print(shader[image_matrix[x][y]], end='')
        print('')
    if options.border is not None:
        print(options.border[0] * window_width)


if __name__ == '__main__':

    def parser_formatter(format_class, **kwargs):
        """
        Use a raw parser to use line breaks, etc
        :param format_class: (class) formatting class
        :param kwargs: (dict) kwargs for class
        :return: (class) formatting class
        """
        try:
            return lambda prog: format_class(prog, **kwargs)
        except TypeError:
            return format_class

    # Get the default font
    system = platform.uname().system.lower()
    if 'darwin' in system:
        system_font = '/System/Library/Fonts/Menlo.ttc'
    elif 'windows' in system:
        system_font = 'C:/Windows/Fonts/consola.ttf'
    elif 'linux' in system:
        if os.path.exists('/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf'):
            system_font = '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf'
        else:
            system_font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    else:
        system_font = None

    parser = argparse.ArgumentParser(description='Create a title',
                                     formatter_class=parser_formatter(
                                         argparse.RawTextHelpFormatter,
                                         indent_increment=4, max_help_position=12, width=160))

    # Image file to read in
    parser.add_argument('-t', '--text',
                        action='store', dest='text', default=None,
                        help='Text to display\n'
                             'Required',
                        required=True)

    # Text of character to render from
    parser.add_argument('-s', '--shader', type=str,
                        action='store', dest='shader',
                        default=' .\'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
                        help='Light to dark characters to use\n'
                             'Default: %(default)s')

    # Text of character to render from
    parser.add_argument('-c', '--chars', type=str,
                        action='store', dest='characters', default=None,
                        help='Specify characters that the system will determine the order of\n'
                             'Overrides -s/--shader')

    parser.add_argument('-b', '--border', type=str,
                        action='store', dest='border', default=None,
                        help='Border character')

    # Font information
    parser.add_argument('-fb', '--font-brightness', type=argparse.FileType('r'),
                        action='store', dest='font_brightness', default=system_font,
                        help='Font used to determine brightness when specifying characters\n'
                             'This should match or be a close approximation of your terminal/console font\n'
                             'Default: %(default)s')

    parser.add_argument('-f', '--font', type=argparse.FileType('r'),
                        action='store', dest='font', default=system_font,
                        help='Font used to write in\n'
                             'Default: %(default)s')

    parser.add_argument('-fh', '--font-height', type=int,
                        action='store', dest='font_height', default=25,
                        help='Font height\n'
                             'Default: %(default)s')

    # Character aspect ratio
    parser.add_argument('-a', '--char-aspect', type=int,
                        action='store', dest='aspect', default=2.4,
                        help='Aspect ratio of the terminal/console character, ADVANCED'
                             'Default: %(default)s\n'
                             'Adjust if aspect ration of the image feels off.  Height / width of a character block')

    # Black/white
    parser.add_argument('-i', '--invert',
                        action='store_true', dest='black_on_white', default=False,
                        help='Invert black/white\n'
                             'Default: %(default)s')

    options = parser.parse_args()

    main()
