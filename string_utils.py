def reverse_string(text):
	"""reverse_string("Hello") -> "olleH" """
	if not isinstance(text, str):
		raise TypeError("reverse_string expects a string")
	return text[::-1]


def is_palindrome(text):
	"""is_palindrome("madam") -> True. Ignores upper/lower case."""
	if not isinstance(text, str):
		raise TypeError("is_palindrome expects a string")
	cleaned = text.lower()
	return cleaned == reverse_string(cleaned)
