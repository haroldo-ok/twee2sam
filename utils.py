from fnmatch import fnmatch

def decodePrettyLink(str):
	"""
	separate PrettyLinks' label and URI

	@param str (str): PrettyLink
	@return (dict): label and URI
	@raise ValueError: invalid PrettyLink
	"""
	if str.startswith("[[") and str.endswith("]]"):
		link = {}
		label, uri = str[2:-2].split("|")
		return { "label": label, "uri": uri }
	else:
		raise ValueError("invalid PrettyLink")

def trimURI(uri): # TODO: properly normalize URI
	"""
	strip non-essential trailing characters from URI

	@param uri (str): URI
	@return (str): uniform URI
	"""
	uri = uri.split("#", 1)[0]
	uri = uri.rstrip("/").lower()
	return uri

def matchPatterns(term, patterns): # TODO: rename
	for pattern in patterns:
		if fnmatch(term, pattern):
			return True
	return False
