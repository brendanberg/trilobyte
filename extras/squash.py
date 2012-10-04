from data import Base64

class Squash(Base64):
	@classmethod
	def decode(clz, string):
		return clz.decompress(super(Squash, clz).decode(string))
	
	@classmethod
	def encode(clz, byteString):
		return super(Squash, clz).encode(clz.compress(byteString))
	
	@classmethod
	def compress(clz, string):
		'''
		Return a compressed ASCII string by run-length encoding a Burrows-
		Wheeler transform of the input string.
		'''
		return clz._rle_encode(clz._bwt_encode(string))
	
	@classmethod
	def decompress(clz, bytes):
		'''
		Return a decompressed ASCII string by reconstructing a run-length
		encoded and B-W transformed bytestring.
		'''
		return clz._bwt_decode(clz._rle_decode(bytes))
	
	@staticmethod
	def _bwt_encode(string):
		'''
		Return a Burrows-Wheeler transform of the input string.
		(http://en.wikipedia.org/wiki/Burrows–Wheeler_transform)
		
		A Burrows-Wheeler transform is a reversible transformation that sorts a
		string so its characters are in lexicographic order. We make a table of
		all rotations of the original string and sort the rows. The transformed
		result is the sequence of final characters from each row.
		'''
		assert '\0' not in string, "Input string cannot contain nul character ('\0')"
		string += '\0'
		table = [string[i:] + string[:i] for i in range(len(string))]
		table.sort()
		return ''.join([row[-1:] for row in table])
	
	@staticmethod
	def _bwt_decode(string):
		'''
		Return the original string from a Burrows-Wheeler transformed string.
		'''
		# Naive implementation
		table = [''] * len(string)
		for i in range(len(string)):
			table = [string[i] + table[i] for i in range(len(string))]
			table.sort()
		s = [row for row in table if row.endswith('\0')][0]
		return s.rstrip('\0')
	
	@staticmethod
	def _rle_encode(string):
		'''Return a run-length encoded string
		
		A single character in the range 0 - 127 (ASCII) is encoded as itself.
		
		Characters in the range from 128 - 255 are broken into two bytes. The
		high-order bits are prefixed with the codeword '1110' and the low-
		order bits are prefixed with the codeword '1100'.
		
		+---+---+---+---+---+---+---+---+ +---+---+---+---+---+---+---+---+
		| 1 | 1 | 1 | 0 | . | . | . | . | | 1 | 1 | 0 | 0 | . | . | . | . |
		+---+---+---+---+---+---+---+---+ +---+---+---+---+---+---+---+---+
		
		Therefore, the byte '10110111' would be encoded as '11101011 11000111'
		
		Runs of two through 65 characters are encoded as above, with a prefix
		byte that identifies the length of the run. A run length byte itself
		is prefixed with the codeword '10'. Since runs of length zero or one
		are not possible, we subtract 2 from the run length before encoding
		the byte.
		
		+---+---+---+---+---+---+---+---+
		| 1 | 0 | . | . | . | . | . | . |
		+---+---+---+---+---+---+---+---+
		
		Therefore, a run of length 26 would be encoded as '10011000'.
		'''
		
		count = 1
		prev = None
		encoded = ''
		
		def encode_run(char, count):
			if ord(char) >= 127:
				high, low = ((ord(char) & 0xF0) >> 4, ord(char) & 0x0F)
				enc = chr(0xE0 | 0x0F & high) + chr(0xC0 | 0x0F & low)
			else:
				enc = char
			
			if count == 1:
				return enc
			else:
				return chr(0x80 | (count - 2)) + enc
		
		for ch in string:
			if prev == None:
				prev = ch
				continue
			elif prev == ch:
				count += 1
			
			if ch != prev or count == 65:
				encoded += encode_run(prev, count)
				count = 1
				prev = ch
		
		encoded += encode_run(prev, count)
		return encoded
	
	@staticmethod
	def _rle_decode(string):
		'''Return the expanded form of a run-length encoded string'''
		
		decoded = ''
		temp = 0
		length = 0
		
		for ch in string:
			byte = ord(ch)
			if byte & 0x80 == 0x00:
				# ch is a single character.
				if length == 0:
					decoded += ch
				else:
					decoded += ch * length
				
				length = 0
			elif byte & 0xF0 == 0xE0:
				# ch is the high-order half of a character in the range
				# 128 - 255. Bitshift the lowest four bytes of ch and
				# place it in a temporary variable.
				temp = ((byte & 0x0F) << 4)
			elif byte & 0xF0 == 0xC0:
				# ch is the low-order half of a character in the range
				# 128 - 255. The high-order half is in a temporary variable.
				# Bitwise or the remaining bits onto the variable and append
				# the character value onto the string.
				temp |= byte & 0x0F
				
				if length == 0:
					decoded += chr(temp)
				else:
					decoded += chr(temp) * length
				
				length = 0
			elif byte & 0xC0 == 0x80:
				# ch is an encoded run length. We only encode runs of more
				# than two characters, so we decode the value by adding two
				# to the value in the lowest six bits of the masked byte.
				length = (byte & 0x4F) + 2
			else:
				raise ValueError('Illegal string')
		
		return decoded
