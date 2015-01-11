import re



class Room:

	def __init__(self, kind, ident, name, attrs):
		self.kind = kind
		self.ident = ident
		self.name = name
		self.attrs = attrs

	def simple_attr(self, attr_name):
		if not attr_name in self.attrs:
			return None

		return "\n".join([ln.strip() for ln in "\n".join(self.attrs[attr_name]).replace('"', '').split('\n')])


source = open('Advent.inf.txt').read()
first_pass = re.findall(r"""^(\w+)\s+(\w+)\s*(?:"(.*?)")?((?:\s*\w+(?:\s+(?:\w+|'[^']+'|"[^"]+"|\[;[^\]]*]))+,?)+);""", source, re.MULTILINE)
attr_regex = re.compile(r"""\s*(\w+)((?:\s+(?:\w+|'[^']+'|"[^"]+"|\[;[^\]]*]))+),?""")
attr_value_regex = re.compile(r"""\s+(\w+|'[^']+'|"[^"]+"|\[;[^\]]*]),?""")

rooms = []
for first_pass_tuple in first_pass:
	kind, ident, name, rest = first_pass_tuple
	pre_attrs = attr_regex.findall(rest)
	attrs = {}

	for name, value_string in pre_attrs:
		attrs[name] = attr_value_regex.findall(value_string)

	rooms.append(Room(kind, ident, name, attrs))


out = open('Advent.twee', 'w')

directions = {
	'n_to': 'North', 's_to': 'South',
	'e_to': 'East', 'w_to': 'West',
	'u_to': 'Up', 'd_to': 'Down',
	'in_to': 'Enter', 'out_to': 'Leave'
}
for room in rooms:
	description = room.simple_attr('description')
	if description:
		out.write(':: {0}\n'.format(room.ident.replace('_', ' ')))
		out.write(description.replace('~', "'").replace('^^', ''))
		out.write('\n')

		for abbrev, name in directions.items():
			target = room.simple_attr(abbrev)
			if target and not target.startswith('[;'):
				out.write('* [[{0}|{1}]]\n'.format(name, target.replace('_', ' ')))

		out.write('\n\n')

out.close()