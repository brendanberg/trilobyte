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
# Version 0.6
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2012

from __future__ import division
from math import log
import re


class Data(object):
	'''The `Data` class is an opaque data object that uses a byte string as a
	backing store. The class provides functions to manipulate data objects and
	generate string representations
	
	'''
	
	def __init__(self, string, encoding=None):
		if encoding:
			self.bytes = encoding.decode(string)
		else:
			assert(isinstance(string, str))
			self.bytes = string
	
	def stringWithEncoding(self, encoding, **kwargs):
		return encoding.encode(self.bytes, **kwargs)
	
	def __str__(self):
		return self.stringWithEncoding(Base64)
	
	def __repr__(self):
		encoded = self.stringWithEncoding(Base64)
		if '\n' in encoded:
			return "Data('''{0}''', Base64)".format(encoded)
		else:
			return "Data('{0}', Base64)".format(encoded)
	
	def __hex__(self):
		return self.stringWithEncoding(Base16)
	
	def __add__(self, other):
		return Data(self.bytes + other.bytes)
	
	__concat__ = __add__
	
	def __iadd__(self, other):
		self.bytes += other.bytes
		return self
	
	def __contains__(self, item):
		return item.bytes in self.bytes
	
	def __eq__(self, other):
		return self.bytes == other.bytes
	
	def __len__(self):
		return len(self.bytes)
	
	def __getitem__(self, key):
		return Data(self.bytes[key])
	
	def __setitem__(self, key, value):
		if isinstance(key, slice):
			start, stop, step = key.indices(len(self.bytes))
			
			if step != 1:
				raise TypeError('cannot modify data contents with a stride')
			
			self.bytes = self.bytes[:start] + value.bytes + self.bytes[stop:]
		elif isinstance(key, int):
			self.bytes = self.bytes[:key] + value.bytes + self.bytes[key+1:]
		else:
			raise TypeError('data indices must be integers or slices')


class Encoding(object):
	'''The `Encoding` class is an abstract base for various encoding types.
	It provides generic left-to-right bitwise conversion algorithms for its
	subclasses. At a minimum, a subclass must override the `alphabet` and
	`base` class properties.
	
	Attempting to instantiate an encoding object will result in a
	`NotImplementedError`:
	
	>>> Encoding()
	Traceback (most recent call last):
		...
	NotImplementedError: Encoding classes cannot be instantiated. ...
	'''
	
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
			try:
				window |= (alphabet.index(ch) << winOffset)
			except ValueError:
				raise ValueError('Illegal character in input string')
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
	
	@classmethod
	def _canonicalRepr(clz, string):
		return super(Base16, clz)._canonicalRepr(string.upper())



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
	
	@classmethod
	def _canonicalRepr(clz, string):
		return super(Base32, clz)._canonicalRepr(string.upper())



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
		' ': '',
		'=': ''
	}
	
	@classmethod
	def encode(clz, byteString, **kwargs):
		if 'alphabet' not in kwargs:
			highIndexChars = kwargs.get('highindexchars', '+/')
			kwargs['alphabet'] = clz.alphabet[:-2] + highIndexChars
		
		string = super(Base64, clz).encode(byteString, **kwargs)
		padding = '=' * (4 - ((len(string) % 4) or 4))
		return string + padding



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
		
		for idx, char in enumerate(byteString[::-1]):
			temp += ord(char) * (256 ** idx)
		
		while temp > 0:
			string += clz.alphabet[temp % 58]
			temp //= 58
		
		return string[::-1]



class Phonetic(Encoding):
	r'''
	Encodes byte strings as sequences of phonetic words and decodes sequences
	of words into byte strings.
	
	Each byte is encoded as one of 256 phonetically distinct words that are
	easy for a human to speak or read. The word list is based on Zachary
	Voase's humanhash word list, but some similar-sounding words have been
	replaced with more distinct alternatives.
	
	
	USAGE REFERENCE
	
	An empty Phonetic-encoded string decodes to an empty byte string.
	
	>>> a = Data('', Phonetic)
	>>> hex(a)
	''
	
	
	A zero value byte string encodes to a Phonetic-encoded string as many words
	as the byte width of the original string.
	
	>>> b = Data('\x00\x00\x00\x00')
	>>> b.stringWithEncoding(Phonetic)
	'abacus abacus abacus abacus'
	
	
	Decoding a Phonetic-encoded string accepts canonical strings (lower case
	words separated by spaces).
	
	>>> c = Data('chicken yankee wolfram asparagus', Phonetic)
	>>> hex(c)
	'26FCF90B'
	
	
	Decoding a Phonetic-encoded string accepts reasonable deviations from the
	canonical string (mixed case, alternative whitespace, hyphens, periods,
	and underscores.)
	
	>>> d = Data('table-tennis COFFEE.CUP Twenty_Three', Phonetic)
	>>> hex(d)
	'D8DC272EE3DF'
	
	
	Re-encoding the data results in the canonicalized word string.
	
	>>> d.stringWithEncoding(Phonetic)
	'table tennis coffee cup twenty three'
	
	
	Words that are not in the word list are invalid.
	
	>>> Data('bandersnatch washington', Phonetic)
	Traceback (most recent call last):
	   ...
	ValueError: Illegal input string
	
	>>> Data('sink-hippopotamus-tennessee', Phonetic)
	Traceback (most recent call last):
	   ...
	ValueError: Illegal input string
	'''
	
	wordList = [
		'abacus', 'alabama', 'alarmist', 'alaska', 'alpha', 'angel', 'apart',
		'april', 'arizona', 'arkansas', 'artist', 'asparagus', 'aspen', 'august',
		'autumn', 'avocado', 'bacon', 'bakerloo', 'batman', 'beer', 'berlin',
		'beryllium', 'black', 'blimp', 'blossom', 'bluebird', 'bravo', 'bulldog',
		'burger', 'butter', 'california', 'carbon', 'cardinal', 'carolina',
		'carpet', 'cat', 'ceiling', 'charlie', 'chicken', 'coffee', 'cola', 'cold',
		'colorado', 'comet', 'connecticut', 'crazy', 'cup', 'dakota', 'december',
		'delaware', 'delta', 'diet', 'don', 'double', 'early', 'earth', 'east',
		'echo', 'edward', 'eight', 'eighteen', 'eleven', 'emma', 'enemy', 'equal',
		'failed', 'fantail', 'fifteen', 'fillet', 'finland', 'fish', 'five', 'fix',
		'floor', 'florida', 'football', 'four', 'fourteen', 'foxtrot', 'freddie',
		'friend', 'fruit', 'gee', 'georgia', 'glucose', 'golf', 'green', 'great',
		'hamper', 'happy', 'harry', 'hawaii', 'helium', 'high', 'hot', 'hotel',
		'hydrogen', 'idaho', 'illinois', 'india', 'indigo', 'ink', 'iowa',
		'island', 'item', 'jersey', 'jig', 'jogger', 'juliet', 'july', 'jupiter',
		'kansas', 'kentucky', 'kilo', 'king', 'kitten', 'lactose', 'lake', 'lamp',
		'lemon', 'leopard', 'lima', 'lion', 'lithium', 'london', 'louisiana',
		'low', 'magazine', 'magnesium', 'maine', 'mango', 'march', 'mars',
		'maryland', 'massachusetts', 'may', 'mexico', 'michigan', 'mike',
		'minnesota', 'mirror', 'mississippi', 'missouri', 'mobile', 'mockingbird',
		'monkey', 'montana', 'moon', 'mountain', 'multiply', 'music', 'nebraska',
		'neptune', 'network', 'nevada', 'nine', 'nineteen', 'nitrogen', 'north',
		'november', 'nuts', 'october', 'ohio', 'oklahoma', 'one', 'orange',
		'oranges', 'oregon', 'oscar', 'oven', 'oxygen', 'paper', 'paris', 'pasta',
		'pennsylvania', 'pip', 'pizza', 'pluto', 'potato', 'princess', 'purple',
		'quebec', 'queen', 'quiet', 'red', 'river', 'robert', 'robin', 'romeo',
		'rugby', 'sad', 'salami', 'saturn', 'september', 'seven', 'seventeen',
		'shade', 'sierra', 'single', 'sink', 'six', 'sixteen', 'skylark', 'snake',
		'social', 'sodium', 'solar', 'south', 'spaghetti', 'speaker', 'spring',
		'stairway', 'steak', 'stream', 'summer', 'sweet', 'table', 'tango', 'ten',
		'tennessee', 'tennis', 'texas', 'thirteen', 'three', 'timing', 'triple',
		'twelve', 'twenty', 'two', 'uncle', 'undone', 'uniform', 'uranus', 'utah',
		'vegan', 'venus', 'vermont', 'victor', 'video', 'violet', 'virginia',
		'washington', 'west', 'whiskey', 'white', 'william', 'windmill', 'winter',
		'wisconsin', 'wolfram', 'wyoming', 'xray', 'yankee', 'yellow', 'zebra',
		'zulu'
	]

	wordMap = {
		'abacus': 0x00, 'alabama': 0x01, 'alarmist': 0x02, 'alaska': 0x03,
		'alpha': 0x04, 'angel': 0x05, 'apart': 0x06, 'april': 0x07,
		'arizona': 0x08, 'arkansas': 0x09, 'artist': 0x0A, 'asparagus': 0x0B,
		'aspen': 0x0C, 'august': 0x0D, 'autumn': 0x0E, 'avocado': 0x0F,
		'bacon': 0x10, 'bakerloo': 0x11, 'batman': 0x12, 'beer': 0x13,
		'berlin': 0x14, 'beryllium': 0x15, 'black': 0x16, 'blimp': 0x17,
		'blossom': 0x18, 'bluebird': 0x19, 'bravo': 0x1A, 'bulldog': 0x1B,
		'burger': 0x1C, 'butter': 0x1D, 'california': 0x1E, 'carbon': 0x1F,
		'cardinal': 0x20, 'carolina': 0x21, 'carpet': 0x22, 'cat': 0x23,
		'ceiling': 0x24, 'charlie': 0x25, 'chicken': 0x26, 'coffee': 0x27,
		'cola': 0x28, 'cold': 0x29, 'colorado': 0x2A, 'comet': 0x2B,
		'connecticut': 0x2C, 'crazy': 0x2D, 'cup': 0x2E, 'dakota': 0x2F,
		'december': 0x30, 'delaware': 0x31, 'delta': 0x32, 'diet': 0x33,
		'don': 0x34, 'double': 0x35, 'early': 0x36, 'earth': 0x37, 'east': 0x38,
		'echo': 0x39, 'edward': 0x3A, 'eight': 0x3B, 'eighteen': 0x3C,
		'eleven': 0x3D, 'emma': 0x3E, 'enemy': 0x3F, 'equal': 0x40, 'failed': 0x41,
		'fantail': 0x42, 'fifteen': 0x43, 'fillet': 0x44, 'finland': 0x45,
		'fish': 0x46, 'five': 0x47, 'fix': 0x48, 'floor': 0x49, 'florida': 0x4A,
		'football': 0x4B, 'four': 0x4C, 'fourteen': 0x4D, 'foxtrot': 0x4E,
		'freddie': 0x4F, 'friend': 0x50, 'fruit': 0x51, 'gee': 0x52,
		'georgia': 0x53, 'glucose': 0x54, 'golf': 0x55, 'green': 0x56,
		'great': 0x57, 'hamper': 0x58, 'happy': 0x59, 'harry': 0x5A, 'hawaii': 0x5B,
		'helium': 0x5C, 'high': 0x5D, 'hot': 0x5E, 'hotel': 0x5F, 'hydrogen': 0x60,
		'idaho': 0x61, 'illinois': 0x62, 'india': 0x63, 'indigo': 0x64,
		'ink': 0x65, 'iowa': 0x66, 'island': 0x67, 'item': 0x68, 'jersey': 0x69,
		'jig': 0x6A, 'jogger': 0x6B, 'juliet': 0x6C, 'july': 0x6D, 'jupiter': 0x6E,
		'kansas': 0x6F, 'kentucky': 0x70, 'kilo': 0x71, 'king': 0x72,
		'kitten': 0x73, 'lactose': 0x74, 'lake': 0x75, 'lamp': 0x76, 'lemon': 0x77,
		'leopard': 0x78, 'lima': 0x79, 'lion': 0x7A, 'lithium': 0x7B,
		'london': 0x7C, 'louisiana': 0x7D, 'low': 0x7E, 'magazine': 0x7F,
		'magnesium': 0x80, 'maine': 0x81, 'mango': 0x82, 'march': 0x83,
		'mars': 0x84, 'maryland': 0x85, 'massachusetts': 0x86, 'may': 0x87,
		'mexico': 0x88, 'michigan': 0x89, 'mike': 0x8A, 'minnesota': 0x8B,
		'mirror': 0x8C, 'mississippi': 0x8D, 'missouri': 0x8E, 'mobile': 0x8F,
		'mockingbird': 0x90, 'monkey': 0x91, 'montana': 0x92, 'moon': 0x93,
		'mountain': 0x94, 'multiply': 0x95, 'music': 0x96, 'nebraska': 0x97,
		'neptune': 0x98, 'network': 0x99, 'nevada': 0x9A, 'nine': 0x9B,
		'nineteen': 0x9C, 'nitrogen': 0x9D, 'north': 0x9E, 'november': 0x9F,
		'nuts': 0xA0, 'october': 0xA1, 'ohio': 0xA2, 'oklahoma': 0xA3, 'one': 0xA4,
		'orange': 0xA5, 'oranges': 0xA6, 'oregon': 0xA7, 'oscar': 0xA8,
		'oven': 0xA9, 'oxygen': 0xAA, 'paper': 0xAB, 'paris': 0xAC, 'pasta': 0xAD,
		'pennsylvania': 0xAE, 'pip': 0xAF, 'pizza': 0xB0, 'pluto': 0xB1,
		'potato': 0xB2, 'princess': 0xB3, 'purple': 0xB4, 'quebec': 0xB5,
		'queen': 0xB6, 'quiet': 0xB7, 'red': 0xB8, 'river': 0xB9, 'robert': 0xBA,
		'robin': 0xBB, 'romeo': 0xBC, 'rugby': 0xBD, 'sad': 0xBE, 'salami': 0xBF,
		'saturn': 0xC0, 'september': 0xC1, 'seven': 0xC2, 'seventeen': 0xC3,
		'shade': 0xC4, 'sierra': 0xC5, 'single': 0xC6, 'sink': 0xC7, 'six': 0xC8,
		'sixteen': 0xC9, 'skylark': 0xCA, 'snake': 0xCB, 'social': 0xCC,
		'sodium': 0xCD, 'solar': 0xCE, 'south': 0xCF, 'spaghetti': 0xD0,
		'speaker': 0xD1, 'spring': 0xD2, 'stairway': 0xD3, 'steak': 0xD4,
		'stream': 0xD5, 'summer': 0xD6, 'sweet': 0xD7, 'table': 0xD8,
		'tango': 0xD9, 'ten': 0xDA, 'tennessee': 0xDB, 'tennis': 0xDC,
		'texas': 0xDD, 'thirteen': 0xDE, 'three': 0xDF, 'timing': 0xE0,
		'triple': 0xE1, 'twelve': 0xE2, 'twenty': 0xE3, 'two': 0xE4, 'uncle': 0xE5,
		'undone': 0xE6, 'uniform': 0xE7, 'uranus': 0xE8, 'utah': 0xE9,
		'vegan': 0xEA, 'venus': 0xEB, 'vermont': 0xEC, 'victor': 0xED,
		'video': 0xEE, 'violet': 0xEF, 'virginia': 0xF0, 'washington': 0xF1,
		'west': 0xF2, 'whiskey': 0xF3, 'white': 0xF4, 'william': 0xF5,
		'windmill': 0xF6, 'winter': 0xF7, 'wisconsin': 0xF8, 'wolfram': 0xF9,
		'wyoming': 0xFA, 'xray': 0xFB, 'yankee': 0xFC, 'yellow': 0xFD,
		'zebra': 0xFE, 'zulu': 0xFF
	}
	
	@classmethod
	def setWordList(clz, wordList):
		if len(wordList) != 256:
			raise Exception()
		
		clz.wordList = list(wordList)
		clz.wordMap = {word: count for count, word in enumerate(wordList)}
	
	@classmethod
	def decode(clz, string):
		string = clz._canonicalRepr(string)
		wordlist = re.findall(r'\w+', string)
		
		result = ''
		
		for word in wordlist:
			if word not in clz.wordMap:
				raise ValueError('Illegal input string')
			
			result += chr(clz.wordMap[word])
		
		return result
	
	@classmethod
	def encode(clz, byteString):
		result = []
		
		for ch in byteString:
			result.append(clz.wordList[ord(ch)])
		
		return ' '.join(result)
	
	@classmethod
	def _canonicalRepr(clz, string):
		return re.sub(r'[\W_]', ' ', string).lower()



if __name__ == '__main__':
	import doctest
	
	options = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
	
	doctest.testmod(optionflags=options)
	doctest.testfile('README.md', optionflags=options, globs=globals())
	doctest.testfile('documentation/custom_encoding.md', optionflags=options, globs=globals())
	doctest.testfile('tests/tests.md', optionflags=options, globs=globals())
