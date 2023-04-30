#!/usr/bin/env python3

"""
Script:	title.py
Date:	2020-05-04

Platform: MacOS/Windows/Linux

Description:
Print a title
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Developer'

import os
import platform

from PIL import Image, ImageFont, ImageDraw, ImageStat, ImageChops


class Title:
    def __init__(self, text=None,
                 characters='.\'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
                 character_aspect=2.4,
                 font_for_brightness=None, font_path=None, font_size=20,
                 invert=False):
        """
        Initialise
        :param text: (string) Text to render (optional)
        :param characters: (string) Characters to render with (optional)
        :param character_aspect: (float) Width to height ration, ex 2.4 (optional)
        :param font_path: (string) Path to font file to render with (optional)
        :param font_for_brightness: (string) Path to font file to evaluate brightness (optional)
        :param font_size: (int) Font size (optional)
        :param invert: (bool) Invert the text black/white (optional)
        :return: (void)
        """

        # Get the default font
        system = platform.uname().system.lower()
        if 'darwin' in system:
            self.system_font = '/System/Library/Fonts/Menlo.ttc'
        elif 'windows' in system:
            self.system_font = 'C:/Windows/Fonts/consola.ttf'
        elif 'linux' in system:
            if os.path.exists('/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf'):
                self.system_font = '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf'
            else:
                self.system_font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        else:
            print('Could not determine a system font, Set before printing')
            self.system_font = None

        # Set default characters
        self.characters = str(characters)

        # Set the default character aspect ration
        self.character_aspect = character_aspect

        # Set the default font used for rendering
        if font_path is None:
            self.font_path = self.system_font
        else:
            if os.path.exists(font_path):
                self.font_path = font_path
            else:
                print('Path to {} cannot be accessed/found'.format(font_path))
                self.font_path = self.system_font

        # Set default font used for brightness
        if font_for_brightness is None:
            self.font_for_brightness = self.system_font
        else:
            if os.path.exists(font_for_brightness):
                self.font_for_brightness = font_for_brightness
            else:
                print('Path to {} cannot be accessed/found'.format(font_for_brightness))
                self.font_for_brightness = self.system_font

        # Set the default font size
        self.font_size = font_size

        # Set default Black on white
        self.invert = invert

        # Calculate gradient and store so we do not need to do each time
        self.shader, self.shader_length = self.__get_font_order(self.characters, self.font_for_brightness)

        # Render any text given
        if text is not None:
            self.print(text)

    def __get_font_order(self, characters, font_for_brightness):
        """
        Calculate the character order from brightest (empty) to darkest (full)
        :param characters: (string) Characters to order
        :param font_for_brightness: (string) Path to font file to evaluate brightness (optional)
        :return: (list)(string) Characters, (int) Length of list
        """
        # Validate font path
        if not os.path.exists(font_for_brightness):
            print('Path to {} cannot be accessed/found'.format(font_for_brightness))
            font_for_brightness = self.system_font

        # Load font to be used
        font = ImageFont.truetype(font_for_brightness, 18)

        # Filter out duplicates
        characters = list(set(characters))
        if ' ' not in characters:
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

        shader_length = len(shader) - 1

        return shader, shader_length

    def print(self, text,
              characters=None, character_aspect=None,
              font_path=None, font_for_brightness=None, font_size=None,
              invert=None):
        """
        Print text
        :param text: (string) Text to render
        :param characters: (string) Characters to render with (optional)
        :param character_aspect: (float) Width to height ration, ex 2.4 (optional)
        :param font_path: (string) Path to font file to render with (optional)
        :param font_for_brightness: (string) Path to font file to evaluate brightness (optional)
        :param font_size: (int) Font size (optional)
        :param invert: (bool) Invert the text black/white (optional)
        :return: (void)
        """

        dynamic_sizing = False

        # If new values are not passed resort to default values
        characters = self.characters if characters is None else characters
        character_aspect = self.character_aspect if character_aspect is None else character_aspect
        font_path = self.font_path if font_path is None else font_path
        font_for_brightness = self.font_for_brightness if font_for_brightness is None else font_for_brightness
        font_size = self.font_size if font_size is None else font_size
        invert = self.invert if invert is None else invert

        # Validate data
        if not os.path.exists(font_path):
            print('Path to {} cannot be accessed/found'.format(font_path))
            font_path = self.system_font

        # Recalculate the shader if relevant options are passed
        if (characters or font_for_brightness) is not None:
            shader, shader_length = self.__get_font_order(characters, font_for_brightness)
        else:
            shader, shader_length = self.shader, self.shader_length
        if invert:
            shader = shader[::-1]

        # Get terminal/console dimensions
        window_width, window_height = os.get_terminal_size()

        # If size is 0, dynamically size to window
        if font_size == 0:
            font_size = int(window_width / len(text) * 2)
            dynamic_sizing = True

        # Create an image of the text
        font = ImageFont.truetype(font_path, font_size)
        image = Image.new('L', (window_width * 10, int(font_size * 1.1)), 0)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, font=font, fill=255, align='left')

        # Calculate new sizes and crop to size
        image_width, image_height = image.size
        if dynamic_sizing:
            # Crop empty space
            image_black = Image.new(image.mode, image.size, 0)
            diff = ImageChops.difference(image, image_black)
            image_bounds = diff.getbbox()
            image = image.crop((image_bounds[0], 0, image_bounds[2], image_height))

            new_height = int((font_size / character_aspect) * window_width / (image_bounds[2] - image_bounds[0]))
        else:
            # Crop to window
            image = image.crop((0, 0, window_width, image_height))
            new_height = int(font_size / character_aspect)

        # Resize image
        image = image.resize((window_width, new_height))

        # Get pixel data
        image_data = image.getdata()

        # Break image into a matrix of perceived values
        for y in range(new_height):
            for x in range(window_width):
                image_pixel = image_data.getpixel((x, y))
                image_contrast = int((image_pixel/255) * shader_length)
                print(shader[image_contrast], end='')
            #print()

    def set_characters(self, characters='.\'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'):
        """
        Set the default characters to use to render the text
        :param characters: (string) Characters to render with
        :return: (void)
        """
        self.characters = str(characters)
        self.shader, self.shader_length = self.__get_font_order(self.characters, self.font_for_brightness)

    def set_character_aspect(self, character_aspect=2.4):
        """
        Set the default character aspect ratio
        :param character_aspect: (float) Width to height ration, ex 2.4
        :return: (void)
        """
        self.character_aspect = float(character_aspect)

    def set_font_for_brightness(self, font_for_brightness=None):
        """
        Set the default font for determining brightness, should approximate terminal/console font
        :param font_for_brightness: (string) Path to font file
        :return: (bool) Successfully set
        """
        if font_for_brightness is not None:
            self.font_for_brightness = font_for_brightness
        else:
            self.font_for_brightness = self.system_font
        self.shader, self.shader_length = self.__get_font_order(self.characters, self.font_for_brightness)

    def set_font_path(self, font_path=None):
        """
        Set the default font for rendering
        :param font_path: (string) Path to font file
        :return: (bool) Successfully set
        """
        if font_path is not None:
            self.font_path = font_path
            return True
        else:
            self.font_path = self.system_font
            return False

    def set_font_size(self, font_size=20):
        """
        Set the default font size
        :param font_size: (int) Font size
        :return: (void)
        """
        self.font_size = int(font_size)

    def set_invert(self, invert=False):
        """
        Set whether the default is to invert or not
        :param invert: (bool) To invert text
        :return: (void)
        """
        self.invert = bool(invert)
