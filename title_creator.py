#!/usr/bin/env python3

"""
Script:	title_creator2.py
Date:	2021-07-10

Platform: MacOS/Windows/Linux

Description:
Print a title
A complete rewrite of title_creator
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2022, thedzy.com'
__license__ = 'GPL'
__version__ = '2.0'
__maintainer__ = 'thedzy.com'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Developer'

import argparse
import os
import platform
import string

import numpy
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
import json


def main() -> None:
    # Create the directory to dump debug images
    if options.debug_dump:
        os.makedirs(options.debug_dump, exist_ok=True)

    # Get character set
    if not options.characters:
        options.characters = string.digits + string.punctuation + string.ascii_letters

    # Add a blank character if not included
    if not options.no_blank and ' ' not in options.characters:
        options.characters += ' '

    characters = {}
    if options.load:
        try:
            characters = json.load(open(options.load, 'r'))
            first_key, first_value = next(iter(characters.items()))
            options.resolution = len(first_value)

            for character in characters:
                characters[character] = [numpy.array(inner_array) for inner_array in characters[character]]
        except FileNotFoundError:
            print(f'File not found: {options.load}')
            exit(1)
    else:
        # Dimension to create a sample character
        sample_height, sample_width = 200, 200

        # Load font to be used for brightness
        font = ImageFont.FreeTypeFont(options.font_brightness.name, sample_height, layout_engine=ImageFont.Layout.BASIC)

        # Render a sample character to get crop dimensions
        character_image = Image.new('L', (sample_width * 2, sample_height * 2), 0)
        draw = ImageDraw.Draw(character_image)

        # Draw each character over each other
        for index, char in enumerate(options.characters):
            # Draw the character in the center of the image
            draw.text((0, 0), char, font=font, fill=256)

        # Get the bounding box of the characters
        bounding_box = character_image.getbbox()
        upper_left = bounding_box[0:2]
        lower_right = bounding_box[2:4]

        # Get brightness of a character in matrix
        for supplied_char in options.characters:
            characters[supplied_char] = image_chopper(supplied_char, font, upper_left, lower_right)

    # Get window/terminal size
    try:
        window_width, _ = os.get_terminal_size()
    except:
        window_width = 180

    # Load font to be used
    font = ImageFont.FreeTypeFont(options.font.name, options.font_height, layout_engine=ImageFont.Layout.BASIC)

    # If specified, set font variation, on error list variations
    font = font.font_variant()
    # print(font.get_variation_axes())
    if options.font_variation:
        try:
            font.set_variation_by_name(options.font_variation)
        except (ValueError, OSError):
            try:
                variations = font.get_variation_names()
                print(f'Choose from the following variations:')
                for variation in variations:
                    print(f'\t - {variation.decode()}')

            except OSError:
                print('Font does not support variations')

    # Get height
    _, top, _, bottom = font.getbbox(string.ascii_letters)
    text_height = int((bottom - top) * 1.4)

    # Generate images for each lines
    text_images = []
    for line in options.text.split('\n'):
        # Skip blank lines
        if len(line.strip()) == 0:
            continue

        # Render text
        text_image = Image.new('L', (window_width * 20, text_height), 0)
        draw = ImageDraw.Draw(text_image)
        draw.text((0, 0), line, font=font, fill=255, align='left')

        # Crop empty space
        image_black = Image.new(text_image.mode, text_image.size, 0)
        diff = ImageChops.difference(text_image, image_black)
        image_bounds = diff.getbbox()

        # Crop out empty space on the width and height
        text_image = text_image.crop((image_bounds[0], image_bounds[1], image_bounds[2], image_bounds[3]))

        text_images.append(text_image)

    # Find the largest image to scale evenly
    image_width = 0
    for text_image in text_images:
        # Get image size
        text_image_width, _ = text_image.width, text_image.height
        image_width = text_image_width if text_image_width > image_width else image_width

    # Find the scale for scaling down
    resize_ratio = window_width / image_width if image_width > window_width - 2 else 1

    # Save character map
    if options.save is not None:
        for character in characters:
            characters[character] = characters[character].tolist()
        answer = ''
        while answer != 'yes' and answer != 'no' and answer != 'y' and answer != 'n':
            if os.path.exists(options.save):
                print(f'File {options.save} already exists. Do you want to replace it? (yes/no): ', end='')
                answer = input().lower()
                if answer == 'no' or answer == 'n':
                    print('Aborting')
                    exit(0)
        json.dump(characters, open(options.save, 'w+'))

    # Print Characters
    for text_image in text_images:
        image_width, image_height = text_image.width, text_image.height

        # Scale it smaller than 1 to 1 and by resolution
        text_image = text_image.resize((int(image_width * resize_ratio * options.resolution),
                                        int(image_height * resize_ratio * options.resolution / options.aspect)))

        if options.debug_dump:
            text_image.save(f'{options.debug_dump}/__title.jpg')

        # Invert?
        if options.black_on_white:
            text_image = ImageOps.invert(text_image)

        # Get final image size
        image_width = text_image.width
        image_height = text_image.height

        # Write image to screen
        line = 0
        while line < image_height:
            # For section/"column" in "row"
            printed_line = ''
            for index in range(image_width // options.resolution):
                index = index * options.resolution

                # Section of image (resolution * resolution)
                pattern = numpy.zeros((options.resolution, options.resolution))
                for col in range(options.resolution):
                    for row in range(options.resolution):
                        try:
                            pattern[row][col] = text_image.getpixel((index + col, line + row))
                        except IndexError:
                            pattern[row][col] = 0

                # Find matching character for section append string
                matching_algorithm = globals()[f'find_match_{options.algorithm}']
                char_invert, char_clear = '\033[7m', f'\033[0m'
                character, inverted = matching_algorithm(pattern, characters, resolution=options.resolution)
                # shade, shade_end = get_shade(pattern, options.shade, inverted)
                printed_line += f'{char_invert if inverted else ""}{character}{char_clear if inverted else ""}'
            print(printed_line)

            # Jump to the next "row" of pixels in the image
            line += options.resolution


def get_shade(pattern: float, offset: int, inverted: bool) -> int:
    """
    Calculate ansi code for 0-256 brightness value
    :param brightness: (float) 0-256 brightness
    :return: (str, str) Ansi code for color, ansi code for reset
    """
    shade_start = '\033[7m' if inverted else ''
    shade_end = f'\033[0m'

    if offset == 0:
        return shade_start, shade_end

    if not inverted:
        pattern = 255 - pattern

    brightness = numpy.average(pattern)
    brightness = 256 - brightness
    ansi_value = 232 + round(brightness / (256 / 23))
    ansi_value = 232 + (23 - (round(brightness / (256 / 23))))

    # Floor and ceiling the value to 232, 255
    ansi_value = min(max(ansi_value + (23 - offset), 232), 255)
    shade = f'\033[38;5;{ansi_value}m'

    if inverted:
        shade_start = shade + shade_start

    return shade_start, shade_end


def find_match_norm(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using numpy linear algebra
    :param pattern: 2d array of values
    :param characters: (dict) Characters ans 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    matched_character, matched_matrix = ' ', None
    min_distance = numpy.inf
    for character, matrix in characters.items():
        distance = numpy.linalg.norm(pattern - matrix)
        if distance < min_distance:
            min_distance = distance
            matched_character, matched_matrix = character, matrix

    # Return best match
    return matched_character, invert


def find_match_inorm(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using numpy linear algebra
    Compare again inverted character
    Makes marginally better results when using block characters at a slight cost of performance 5-6%
    :param pattern: 2d array of values
    :param characters: (dict) Characters and 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    matched_character, matched_matrix = ' ', None
    min_distance = numpy.inf
    for character, matrix in characters.items():
        for mode in (False, True):
            if mode:
                matrix = 255 - matrix
            distance = numpy.linalg.norm(pattern - matrix)
            if distance < min_distance:
                min_distance = distance
                matched_character, matched_matrix, invert = character, matrix, mode

    # Return best match
    return matched_character, invert


def find_match_outline(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using count of close matches
    :param pattern: 2d array of values
    :param characters: (dict) Characters and 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    threshold = kwargs['image_width']
    best_match, matched_character = 0, ' '
    for character, matrix in characters.items():
        new_matrix = numpy.abs(pattern - matrix)
        mask = (new_matrix < threshold) | (new_matrix > (256 - threshold))
        distance = numpy.count_nonzero(mask)
        if distance > best_match:
            best_match = distance
            matched_character, matched_matrix = character, matrix

    # Return best match
    return matched_character, invert


def find_match_low(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using count of close low matches
    :param pattern: 2d array of values
    :param characters: (dict) Characters and 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    threshold = 40
    best_match, matched_character = 0, ' '
    for character, matrix in characters.items():
        new_matrix = numpy.abs(pattern - matrix)
        distance = sum(1 for x in new_matrix for y in x if y < threshold)
        if distance > best_match:
            best_match = distance
            matched_character, matched_matrix = character, matrix

    # Return best match
    return matched_character, invert


def find_match_abs(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using numpy sum(abs(matrix-matrix))
    :param pattern: 2d array of values
    :param characters: (dict) Characters ans 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    best_match = numpy.infty
    for character, matrix in characters.items():
        simularity = numpy.sum(numpy.abs(pattern - matrix))
        if simularity < best_match:
            matched_character = character
            best_match = simularity

    # Return best match
    return matched_character, invert


def find_match_iabs(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using numpy sum(abs(matrix-matrix))
    Compare again inverted character
    Makes marginally better results when using block characters at a slight cost of performance 5-6%
    :param pattern: 2d array of values
    :param characters: (dict) Characters and 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    best_match = numpy.infty
    for character, matrix in characters.items():
        for mode in (False, True):
            if mode:
                matrix = 255 - matrix
            simularity = numpy.sum(numpy.abs(pattern - matrix))
            if simularity < best_match:
                best_match = simularity
                matched_character, matched_matrix, invert = character, matrix, mode

    # Return best match
    return matched_character, invert


def find_match_abs2(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using numpy filtering for count of values with less than 64 difference
    :param pattern: 2d array of values
    :param characters: (dict) Characters ans 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    best_match = numpy.infty
    for character, matrix in characters.items():
        mask = (numpy.abs(pattern - matrix) > 64)
        similarity = numpy.count_nonzero(mask)

        if similarity < best_match:
            matched_character = character
            best_match = similarity

    # Return best match
    return matched_character, invert


def find_match_binary(pattern: numpy.ndarray, characters: dict, **kwargs: dict) -> str:
    """
    Compare a pattern and find the match in the character set using numpy binary matching
    :param pattern: 2d array of values
    :param characters: (dict) Characters ans 2d arrays
    :param resolution: (int) Array size
    :return:
    """
    invert = False

    best_match = numpy.infty
    for character, matrix in characters.items():
        new_pattern = numpy.interp(pattern, (0.0, 256.0), (0, 2)).astype(int)
        new_matrix = numpy.interp(matrix, (0.0, 256.0), (0, 2)).astype(int)
        mask = (numpy.abs(new_pattern - new_matrix) == 1)
        similarity = numpy.count_nonzero(mask)

        if similarity < best_match:
            matched_character = character
            best_match = similarity

    # Return best match
    return matched_character, invert


def image_chopper(character: str, font: ImageFont.FreeTypeFont, top_left: numpy.ndarray,
                  bottom_right: numpy.ndarray) -> numpy.ndarray:
    """
    Chop up image and return 2d array of values
    :param character:
    :param font:
    :param top_left:
    :param bottom_right:
    :return:
    """

    # Get image size
    width, height = bottom_right

    # Create image of character
    character_image = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(character_image)
    draw.text((0, -top_left[1]), character, font=font, fill=255, align='left')

    # Crop to bounds
    character_image = character_image.crop((0, 0, bottom_right[0], bottom_right[1]))
    if options.debug_dump:
        character_image.save(f'{options.debug_dump}/{character}.jpg')

    # Resize to resolution and convert to greyscale
    resized_image = character_image.resize((options.resolution, options.resolution))
    resized_image = resized_image.convert('L')

    # Return matrix of brightness values
    return numpy.asarray(resized_image)


if __name__ == '__main__':

    def value_range(low: int, high: int):
        def check_value(number: int):
            try:
                number = int(number)
            except ValueError:
                raise argparse.ArgumentTypeError(f'{number} is not an integer')
            if number > high:
                print('too high')
                raise argparse.ArgumentTypeError(f'{number} is above the range [{low}, {high}]')
            if number < low:
                print('too low')
                raise argparse.ArgumentTypeError(f'{number} is below the range [{low}, {high}]')
            return number

        return check_value


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
                        help='text to display\n'
                             'required',
                        required=True)

    # Algorithm
    parser.add_argument('-a', '--algorithm',
                        action='store', dest='algorithm', default='abs',
                        choices=['iabs', 'abs', 'abs2', 'norm', 'inorm', 'low', 'outline', 'binary'],
                        help='algorithm to use\n'
                             'choices: %(choices)s\n')

    # Text of character to render from
    parser_char = parser.add_mutually_exclusive_group()
    parser_char.add_argument('-c', '--chars', type=str,
                             action='store', dest='characters', default=None,
                             help='specify characters that the system will used to render the text')

    parser_char.add_argument('--chars-alpha-symbols', default=None, const=string.punctuation,
                             action='store_const', dest='characters',
                             help='use ascii symbols characters %(const)s')

    parser_char.add_argument('-ca', '--chars-alpha', default=None,
                             const=string.ascii_letters + string.digits + string.punctuation,
                             action='store_const', dest='characters',
                             help='use ascii letter characters %(const)s'
                                  'default')

    parser_char.add_argument('-cb', '--chars-blocks', default=None, const='▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐▔▕▖▗▘▙▚▛▜▝▞▟■',
                             action='store_const', dest='characters',
                             help='use ascii block characters %(const)s')

    parser_char.add_argument('-cs', '--chars-shapes', default=None,
                             const='■□▢▣▤▥▦▧▨▩▪▫▬▭▮▯▰▱▲△▴▵▶▷▸▹►▻▼▽▾▿◀◁◂◃◄◅◆◇◈◉◊○◌◍◎●◐◑◒◓◔◕◖◗◘◙◚◛◜◝◞◟◠◡◢◣◤◥◦◧◨◩◪◫◬◭◮◯◰◱◲◳◴◵◶◷◸◹◺◻◼◽◾◿',
                             action='store_const', dest='characters',
                             help='use ascii shape characters %(const)s')

    parser_char.add_argument('-cl', '--chars-lines', default=None,
                             const='─━│┃┄┅┆┇┈┉┊┋┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋╌╍╎╏═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿',
                             action='store_const', dest='characters',
                             help='use ascii line characters %(const)s')

    parser.add_argument('--no-blank',
                        action='store_true', dest='no_blank', default=False,
                        help='do not use a space for empty character\n'
                             'default: %(default)s')

    # Font information
    parser.add_argument('-f', '--font', type=argparse.FileType('r'),
                        action='store', dest='font', default=system_font,
                        help='font used to write in\n'
                             'default: %(default)s')

    parser.add_argument('-fh', '--font-height', type=int,
                        action='store', dest='font_height', default=25,
                        help='font height\n'
                             'default: %(default)s')

    parser.add_argument('-fv', '--font-variation', nargs='?',
                        action='store', dest='font_variation', default=None,
                        help='font variation, ie Italics\n'
                             'default: %(default)s')

    parser.add_argument('-fb', '--font-brightness', type=argparse.FileType('r'),
                        action='store', dest='font_brightness', default=system_font,
                        help='font used to determine brightness when specifying characters\n'
                             'this should match or be a close approximation of your terminal/console font\n'
                             'default: %(default)s')

    # Character aspect ratio
    parser.add_argument('--aspect', type=float,
                        action='store', dest='aspect', default=2.2,
                        help='aspect ratio of the terminal/console character, ADVANCED\n'
                             'represented at 1:x, width:height, a value of 2 would mean pixels and twice as high as wide\n'
                             'default: %(default)s\n'
                             'adjust if aspect ration of the image feels off.  Height / width of a character block\n'
                             'increasing the height will cause the programme to compensate and reduce the height\n')

    # Details
    parser.add_argument('-r', '--resolution', type=int,
                        action='store', dest='resolution', default=15,
                        help='the resolution of each character, more=cpu')

    # Style
    parser.add_argument('-i', '--invert',
                        action='store_true', dest='black_on_white', default=False,
                        help='invert black/white\n'
                             'default: %(default)s')
    parser.add_argument('-s', '--shade',
                        action='store', dest='shade', type=value_range(0, 23), default=0,
                        help='amount of grey shades to use\n'
                             'there are 24 shades of gray (0-23)\n'
                             'default: %(default)s')

    parser.add_argument('--save', default=None,
                        action='store', dest='save',
                        help='save character map to file')
    parser.add_argument('--load', default=None,
                        action='store', dest='load',
                        help='load character map from file')

    # Debug
    parser.add_argument('--debug', default=False,
                        action='store_true', dest='debug',
                        help=argparse.SUPPRESS)

    parser.add_argument('--dump', default=None,
                        action='store', dest='debug_dump',
                        help=argparse.SUPPRESS)

    options = parser.parse_args()

    main()
