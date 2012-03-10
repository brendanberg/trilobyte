Trilobyte
=========

Trilobyte is a collection of classes for storing binary data and converting it
into various base-encoded strings for text representations useful for over-the-
wire transmission.

The library's core consists of the `Data` class, which is an opaque wrapper
class for byte strings. (Using string notation for binary data is perhaps one
of Python's more problematic quirks, but we do not question the BDFL.) In
addition, the `Encoding` class provides an abstract interface for various
encoding implementations. Trilobyte provides classes that implement base 16,
Doug Crockford's base 32, Flickr's base 58, and base 64 encodings.

This document describes the motivation behind the Trilobyte library and high-
level use of the objects the library provides.


Data Programming Guide
----------------------

Data objects are opaque wrappers for a string of bytes. The constructor takes
either an encoded string and an encoding specifier, or a raw byte string.
(Encoding specifiers are discussed later.)


### Creating Data Objects from Raw Bytes

Calling the Data constructor with a raw byte string simply wraps the byte
string with a Data object.

	>>> Data('\xcd\tl\xb2y\xd9Ei\xa3\x02\x13\x02\xf44E\xa3')
	Data('zQlssnnZRWmjAhMC9DRFow==', Base64)

Note that the default representation of a Data object uses the base 64 string
representation of its contents. This is typically more compact than Python's
representation of byte strings, since the overhead of hex escaping non-ASCII
characters in the byte string is avoided.

This form of the constructor is useful when dealing with Python libraries that
represent raw binary data as native strings of bytes. For example, an MD5
digest may be encoded as a Base64 string without going through hexadecimal as
an intermediate step.

	>>> from hashlib import md5
	>>> Data(md5('Hello, world!').digest())
	Data('bNNVbesNpUvKBgtMOUeYOQ==', Base64)


### Creating Data Objects from Encoded Strings

When you're provided with data in specific string encodings, the second form
of the constructor is used. Here, you see a Data object instantiated by
calling the constructor with arguments for the encoded string and an encoding
class.

	>>> Data('5d41402abc4b2a76b9719d911017c592', Base16)
	Data('XUFAKrxLKna5cZ2REBfFkg==', Base64)

### Getting String Representations of Data

Data objects have a `stringWithEncoding` method that takes an encoding object
that determines the output encoding. The code snippet below shows how to create
a Base58 encoded string from Data instance `d` above. 

	>>> dat = Data('ba58b7c4fbe6c19a', Base16)
	>>> dat.stringWithEncoding(Base58)
	'xaN7oqjfR4Y'

Likewise, a raw string of bytes may be converted to Doug Crockford's Base32.

	>>> uid = Data('\x97\x88\xf7V\xd4\x9aHE\x84=\xba\xec\xef\x08\xb88')
	>>> uid.stringWithEncoding(Base32)
	'JY4FENPMK944B11XQBPEY25R70'


### Accessing and Comparing Bytes

The Data object supports sequence operations and returns a new Data object
with the requested byte range:

	>>> d = Data('OLgI7+y6PYRFSLrUVveIlw==', Base64)
	>>> d[10]
	Data('ug==', Base64)
	>>> d[1:6]
	Data('uAjv7Lo=', Base64)

And of course, you can compare byte ranges:

	>>> d[5] == d[10]
	True
	>>> d[6] == d[7]
	False


### Manipulating Data Objects

You can append data objects with the Python `+` operator:

	>>> Data('5ee8da1274a740e1', Base16) + Data('aa347f87669901aa', Base16)
	Data('XujaEnSnQOGqNH+HZpkBqg==', Base64)

Data objects are mutable, so you can set byte values at specific indices.

	>>> h = Data('Hello; world!')
	>>> h[5] = Data(',')
	>>> h.bytes
	'Hello, world!'

Keys may be integers or slices, but slices may not specify strides.

	>>> h[7:12] = Data('atlas')
	>>> h.bytes
	'Hello, atlas!'
	>>> h[::-1] = Data('')
	Traceback (most recent call last):
		...
	TypeError: cannot modify data contents with a stride


More Information
----------------

- The [Trilobyte Class Reference](https://github.com/brendn/Trilobyte/blob/master/documentation/class_reference.md)
is an in-depth look at the classes that make up the Trilobyte library.

- The [Custom String Encoding Tutorial](https://github.com/brendn/Trilobyte/blob/master/documentation/custom_encoding.md)
outlines a number of techniques for extending the Trilobyte library.
