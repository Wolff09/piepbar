#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import logging
from PIL import Image, ImageDraw, ImageFont, ImageChops
from displaydriver import DisplayDriver
from config import *

class Display(object):

	def __init__(self, idle_bg=IDLE_PATH, main_bg=MAIN_PATH, font=FONT_PATH,
				 font_size=14, bold_font=BOLD_PATH, bold_font_size=14):

		self.logger = logging.getLogger("display")

		try:
			self._dither = Image.open(DITHER_PATH)
		except:
			self.logger.critical("Can't open dither mask!")
			sys.exit()

		if not self._dither.size == (160,80):
			self.logger.critical("Wrong image size %s" % self._dither.size)
			sys.exit()

		self._dither = self._dither.convert('1')

		if main_bg:
			try:
				self._main_bg = Image.open(main_bg)
			except:
				self.logger.critical("can't open image file!")
				sys.exit()

			if not self._main_bg.size == (160,80):
				self.logger.critical("Wrong image size %s" % self._main_bg.size)
				sys.exit()

			self._main_bg = self._main_bg.convert('1')
		else:
			self._main_bg = Image.new('1', (160,80), 255)

		if idle_bg:
			try:
				self._idle_bg = Image.open(idle_bg)
			except:
				self.citical("Can't open image file!")
				sys.exit()

			if not self._idle_bg.size == (160,80):
				self.citical("Wrong image size %s" % self._idle_bg.size)
				sys.exit()

			self._idle_bg = self._idle_bg.convert('1')
		else:
			self._idle_bg = Image.new('1', (160,80), 255)

		if font:
			try:
				self._font = ImageFont.truetype(font, font_size)
			except:
				self.citical("Can't load font!")
				sys.exit()

		if bold_font:
			try:
				self._bold_font = ImageFont.truetype(bold_font, bold_font_size)
			except:
				self.logger.critical("Can't load bold font!")
				sys.exit()
		
		try:
			self._displaydriver = DisplayDriver(dummy=DUMMY_DISPLAY)
		except:
			self.logger.critical("Unable to open display!")
			sys.exit()

		self._screen = self._idle_bg.copy()
		self._was_idle = True

		self._viewmsg = False
		self._msgscreen = Image.new('1', (160,80), 255)

	def _draw(self):
		if self._viewmsg:
			self._displaydriver.send_image(self._msgscreen)
		else:
			self._displaydriver.send_image(self._screen)

	def idle(self):
		self._screen = self._idle_bg.copy()
		self._was_idle = True
		self._draw()

	def update(self, name=None, drinks=None, total=0):
		if self._was_idle:
			self._screen = self._main_bg.copy()
			self._was_idle = False
		
		draw = ImageDraw.Draw(self._screen)

		if name:
			draw.rectangle([0,0,159,13],fill=255)
			if len(name) > 22:
				draw.text((1,1),name[:19] + "...",font=self._bold_font)
			else:
				draw.text((1,1),name,font=self._bold_font)


		if drinks:
			draw.rectangle([0,17,159,65],fill=255)

			y = 53
			for i,drink in enumerate(drinks[:-5:-1]):
				# TODO: trimming still not perfect
				if len(drinks)>4 and i == 3:
					draw.text((1,17),"und noch %s mehr..." % (len(drinks)-3),font=self._font)
				else:
					if(len(drink[0]+"%s" % drink[1])>21):
						drink_name = drink[0][:(18 - len("%s" % drink[1]))] + "..."
					else:
						drink_name = drink[0]

					size = self._font.getsize("%.2f" % drink[1])
					draw.text((156-size[0],y),"%.2f" % drink[1],font=self._font)
					draw.text((1,y),drink_name,font=self._font)
				y=y-12

		size = self._font.getsize("Summe: %.2f" % total)
		draw.rectangle([0,67,159,79],fill=255)
		draw.text((156-size[0],68),"Summe: %.2f" % total,font=self._bold_font)

		self._draw()

	def message(self, text, heading=None , delay=DEFAULT_MESSAGE_DELAY, align=DEFAULT_MESSAGE_ALIGN):
		self.message_on(text=text, heading=heading, align=align)
		self.message_off(delay=delay)

	def message_on(self, text, heading=None, align=DEFAULT_MESSAGE_ALIGN, delay=None):
		self._msgscreen = self._screen.copy()
		self._msgscreen = ImageChops.lighter(self._msgscreen,self._dither)
		draw = ImageDraw.Draw(self._msgscreen)

		lines = text.splitlines()
		sizes = [self._font.getsize(x) for x in lines]

		if heading:
			sizes = [self._bold_font.getsize(heading)] + sizes

		textsize = (
			max(s[0] for s in sizes),
			sum(s[1] for s in sizes))

		boxsize = [
			((160-textsize[0])//2-4,
			(80-textsize[1])//2-2),
			((160-textsize[0])//2+textsize[0],
			(80-textsize[1])//2+textsize[1]),
		]

		draw.rectangle(boxsize,outline=0,fill=255)

		ypos = boxsize[0][1]+2
		if heading:
			if align=='center':
				draw.text((79-(sizes[0][0]//2),ypos),heading,font=self._bold_font)
			elif align=='left':
				draw.text((boxsize[0][0]+3,ypos),heading,font=self._bold_font)
			else:
				self.logger.error("Unknown alignment \'%s\'" % align)
			ypos += sizes.pop(0)[1]

		for i in range(len(lines)):
			if align=='center':
				draw.text((78-(sizes[i][0]//2),ypos),lines[i],font=self._font)
			elif align=='left':
				draw.text((boxsize[0][0]+3,ypos),lines[i],font=self._font)
			else:
				self.logger.error("Unknown alignment \'%s\'" % align)
			ypos += sizes[i][1]
		
		self._viewmsg = True
		self._draw()
		if delay and delay > 0: time.sleep(delay)

	def message_off(self, delay=None):
		if delay and delay > 0:
			time.sleep(delay)
		self._viewmsg = False
		self._draw()

