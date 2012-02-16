# An opaque Data class with Base encoding and decoding functionality
# -----------------------------------------------------------------------------
# A collection of classes for storing binary data and converting it into
# various base-encoded strings for text representations useful for
# over-the-wire transmission.
# 
# Includes implementations of Base16, Doug Crockford's Base32, Flickr's
# Base58, and Base64 encodings.
# 
# Documentation at http://github.com/brendn/Trilobyte
# 
# Version 0.4
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2012

from __future__ import division
from math import log


class Data(object):
	def __init__(self, string, encoding=None):
		if encoding:
			self.bytes = encoding.decode(string)
		else:
			self.bytes = string
	
	def stringWithEncoding(self, encoding, **kwargs):
		return encoding.encode(self.bytes, **kwargs)
	
	def __add__(self, other):
		return Data(self.bytes + other.bytes)


class Encoding(object):
	alphabet = ''
	base = 0
	replacements = {}
	
	def __init__(self):
		raise NotImplementedError(
			'Encoding classes cannot be instantiated. Use '
			'Data.stringWithEncoding(Encoding) instead.'
		)
	
	@classmethod
	def decode(clz, string, alphabet=None, ignoreinvalidchars=False):
		if not alphabet:
			alphabet = clz.alphabet
		
		width = int(log(clz.base, 2))
		
		bytes = ''
		window = 0
		winOffset = 16 - width
		
		for ch in clz._canonicalRepr(string):
			window |= (alphabet.index(ch) << winOffset)
			winOffset -= width
			
			if winOffset <= (8 - width):
				bytes += chr((window & 0xFF00) >> 8)
				window = (window & 0xFF) << 8
				winOffset += 8
		
		if window:
			# The padding was wrong, so we throw a tantrum
			raise ValueError('Illegal input string')
		
		# We assembled the byte string in reverse because it's faster
		# to append to a string than to prepend in Python. Reversing a
		# string, on the other hand is Super Fast (TM).
		return bytes
	
	@classmethod
	def encode(
		clz,
		byteString,
		alphabet=None,
		linelength=64,
		lineseparator='\r\n'
	):
		if not alphabet:
			alphabet = clz.alphabet
		
		width = int(log(clz.base, 2))
		string = ''
		lineCharCount = 0
		
		window = 0
		
		maskOffset = 8 - width
		mask = (2 ** width - 1) << maskOffset
		
		for ch in byteString:
			window |= ord(ch)
			
			while maskOffset >= 0:
				string += alphabet[(window & mask) >> maskOffset]
				lineCharCount += 1
				
				if linelength and lineCharCount == linelength:
					string += lineseparator
					lineCharCount = 0
				
				if maskOffset - width >= 0:
					mask >>= width
					maskOffset -= width
				else:
					break
			
			window &= 0xFF
			window <<= 8
			mask <<= 8 - width
			maskOffset += 8 - width
		
		if maskOffset > 8 - width:
			# If there are unencoded characters to the right of the mask, shift
			# the mask all the way right and shift the window the remainder of
			# the mask width to encode a zero-padded character at the end.
			string += alphabet[(window & mask) >> maskOffset]
		
		return string
	
	@classmethod
	def _canonicalRepr(clz, string):
		string = string.upper()
		
		for k, v in clz.replacements.iteritems():
			string = string.replace(k, v)
		
		return string


class Base16(Encoding):
	"Encoder class for your friendly neighborhood hexidecimal numbers."
	
	alphabet = '0123456789ABCDEF'
	base = 16
	
	# Discard hyphens, spaces, carriage returns, and new lines from input.
	replacements = {
		'-': '',
		' ': '',
		'\r': '',
		'\n': '',
		'I': '1',
		'L': '1',
		'O': '0',
		'S': '5',
	}



class Base32(Encoding):
	'''Encoder class for Doug Crockford's Base32 encoding. This is not merely
	Python's `int(encoded, 32)` since Crockford's spec discusses replacements
	for commonly confused characters, rather than a simple extension of the
	alphabet used in hexadecimal. For example, the capital letter I, lower
	case i, and lower case l could all be mistaken for the numeral 1. This
	encoding removes that ambiguity by accepting any of these characters but
	converting to a canonical representation for decoding.

	http://www.crockford.com/wrmg/base32.html
	'''
	
	alphabet = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
	base = 32
	replacements = {
		'-': '',
		' ': '',
		'\r': '',
		'\n': '',
		'I': '1',
		'L': '1',
		'O': '0'
	}



class Base64(Encoding):
	'''Encoder class for a flexible Base 64 encoding. 
	'''
	
	alphabet = (
		'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
	)
	base = 64
	replacements = {
		'\r': '',
		'\n': '',
		'=': ''
	}
	
	@classmethod
	def encode(clz, byteString, **kwargs):
		if 'alphabet' not in kwargs:
			highIndexChars = kwargs.get('highindexchars', '+/')
			kwargs['alphabet'] = clz.alphabet[:-2] + highIndexChars
		
		string = super(Base64, clz).encode(byteString, **kwargs)
		
		string += '=' * (3 - (len(byteString) % 3))
		
		return string
	
	@classmethod
	def _canonicalRepr(clz, string):
		for k, v in clz.replacements.iteritems():
			string = string.replace(k, v)
		
		return string



# The general algorithm defined in the Encoding base class expects encoding
# characters to have integer widths. Base 58 encoding is approximately 5.857
# bits wide. I know, right? Numbers are weird.

class Base58(Encoding):
	'''Encoder class for Flickr's base 58 encoding. Base 58 encoding is similar
	to base 32, but includes upper and lower case letters. Upper case I, lower
	case l, and upper case O are all excluded from the alphabet. Unlike
	Crockford's base 32, base 58 encoding rejects input if it encounters
	characters that are not in the alphabet. (Future versions may include a
	flag to discard invalid characters.)
	
	http://www.flickr.com/groups/api/discuss/72157616713786392
	
	Because this encoding does not convert a fixed-width window of bits into a
	base that is a multiple of two, the conversion process is different from
	the encodings seen above.
	'''
	
	alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
	base = 58
	replacements = {
		'-': '',
		' ': ''
	}
	
	@classmethod
	def decode(clz, string):
		width = int(log(clz.base, 2))
		bytes = ''
		temp = 0
		
		# Because each digit is not a whole number of bits, we are using
		# binary as an intermediary. There should be a better way to do
		# this, but this is the best I can find:
		# http://forums.xkcd.com/viewtopic.php?f=12&t=69664
		
		for idx, char in enumerate(clz._canonicalRepr(string)[::-1]):
			temp += clz.alphabet.index(char) * (58 ** idx)
		
		while temp > 0:
			bytes += chr(temp % 256)
			temp //= 256
		
		# We assembled the byte string in reverse because it's faster
		# to append to a string than to prepend in Python. Reversing a
		# string, on the other hand is Super Fast (TM).
		return bytes[::-1]
	
	@classmethod
	def encode(clz, byteString):
		width = int(log(clz.base, 2))
		string = ''
		temp = 0
		
		# Because each digit is not a whole number of bits, we are using
		# binary as an intermediary. There should be a better way to do
		# this, but this is the best I can find:
		# http://forums.xkcd.com/viewtopic.php?f=12&t=69664
		
		for idx, char in enumerate(byteString[::-1]):
			temp += ord(char) * (256 ** idx)
		
		while temp > 0:
			string += clz.alphabet[temp % 58]
			temp //= 58
		
		return string[::-1]
	
	@classmethod
	def _canonicalRepr(clz, string):
		for k, v in clz.replacements.iteritems():
			string = string.replace(k, v)
		
		return string
