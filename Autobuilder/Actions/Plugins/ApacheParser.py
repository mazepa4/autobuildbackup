import re


class ApacheConfig(object):
    re_comment = re.compile(r"""^#.*$""")
    re_section_start = re.compile(r"""^<(?P<name>[^/\s>]+)\s*(?P<value>[^>]+)?>$""")
    re_section_end = re.compile(r"""^</(?P<name>[^\s>]+)\s*>$""")
    re_section_apache_value = re.compile(r"{(.*?)}")


    def __init__(self, name='', values=[], children = [], section=False):
        self.name = name
        self.children = []
        self.values = values
        self.section = section
        self.index = 0
        self.parent = None

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        return child

    def find(self, path):
        """Return the first element wich matches the path.
        """
        pathelements = path.strip("|").split("|")
        if pathelements[0] == '':
            return self
        return self._find(pathelements)

    def _find(self, pathelements):
        if pathelements:  # there is still more to do ...
            next = pathelements.pop(0)

            values = self.re_section_apache_value.findall(next)
            indexes = self.re_section_apache_value.finditer(next)
            valuePos = []
            for pos in indexes:
                valuePos = pos
            for child in self.children:
                if len(values):
                    if child.name == next[:valuePos.start(0)].strip() and child.values == values[0].split():
                        result = child._find(pathelements)
                        if result:
                            return result
                else:
                    if child.name == next:
                        result = child._find(pathelements)
                        if result:
                            return result
            return None
        else:  # no pathelements left, result is self
            return self

    def findall(self, path):
        """Return all elements wich match the path.
        """
        pathelements = path.strip("/").split("/")
        if pathelements[0] == '':
            return [self]
        return self._findall(pathelements)

    def _findall(self, pathelements):
        if pathelements:  # there is still more to do ...
            result = []
            next = pathelements.pop(0)
            for child in self.children:
                if child.name == next:
                    result.extend(child._findall(pathelements))
            return result
        else:  # no pathelements left, result is self
            return [self]

    def print_r(self, indent=-1):
        """Recursively print node.
                """
        if self.section:
            if indent >= 0:
                print("    " * indent + "<" + self.name + " " + " ".join(self.values) + ">")
            for child in self.children:
                child.print_r(indent + 1)
            if indent >= 0:
                print("    " * indent + "</" + self.name + ">")
        else:
            if indent >= 0:
                print("    " * indent + self.name + " " + " ".join(self.values))

    def biuildNewConfig(self, indent=-1):
        text = ""
        if self.section:
            if indent >= 0 and self.name:
                text = text + "\n" + ("    " * indent + "<" + self.name + " " + " ".join(self.values) + ">")
            for child in self.children:
                text = text + "\n" + child.biuildNewConfig(indent + 1)
            if indent >= 0 and self.name:
                text = text + "\n" + ("    " * indent + "</" + self.name + ">") + "\n"
        else:
            if indent >= 0 and self.name:
                if self.name == "comment":
                    text = text + "\n" + ("    " * indent + " ".join(self.values))
                else:
                    text = text  + ("    " * indent + self.name + " " + " ".join(self.values))
        return text

    @classmethod
    def parse_file(cls, file):
        """Parse a file.
        """
        f = open(file)
        root = cls._parse(f)
        f.close()
        return root

    @classmethod
    def parse_string(cls, string):
        """Parse a string.
        """
        return cls._parse(string.splitlines())

    @classmethod
    def _parse(cls, itobj):
        root = node = ApacheConfig('', section=True)
        for line in itobj:
            line = line.strip()
            if (len(line) == 0) or cls.re_comment.match(line):
                continue

            match = cls.re_section_start.match(line)
            if match:
                values = match.group("value").split()
                new_node = ApacheConfig(match.group("name"), values=values, section=True)
                node = node.add_child(new_node)
                continue
            match = cls.re_section_end.match(line)
            if match:
                if node.name != match.group("name"):
                    raise Exception("Section mismatch: '"+match.group("name")+"' should be '"+node.name+"'")
                node = node.parent
                continue
            values = line.split()
            name = values.pop(0)
            node.add_child(ApacheConfig(name, values=values, section=False))
        return root

    def lookForChilds(self,lines):

        root = None
        if self.index:
            _line = lines[self.index-1].strip()
            startStartMath = self.re_section_start.match(_line)
            values = startStartMath.group("value").split()
            name = startStartMath.group("name")
            root = ApacheConfig(name,values=values, section=True)
        else:
            root = ApacheConfig('', section=True)

        while self.index < len(lines):

            line = lines[self.index].strip()
            if (len(line) == 0):
                self.index = self.index + 1
                continue

            commentMath = self.re_comment.match(line)
            if commentMath:
                values = line.split()
                root.add_child(ApacheConfig("comment", values=values, section=False))
            else:
                startStartMath = self.re_section_start.match(line)
                endStartMath = self.re_section_end.match(line)
                if startStartMath:
                    self.index = self.index + 1
                    node =  self.lookForChilds(lines)
                    if node:
                        root.add_child(node)

                if endStartMath:
                    self.index = self.index + 1
                    return root

                if startStartMath == None and endStartMath == None:

                    values = line.split()
                    name = values.pop(0)
                    root.add_child(ApacheConfig(name, values=values, section=False))

            self.index = self.index + 1
        return root




"""
fileLines = open("/home/ivan/Temp/sites-enabled/ecgapi.sapiensapi.com-le-ssl.conf").readlines()
config = ApacheConfig("api",section=True)
root = config.lookForChilds(fileLines)
result = root.find("IfModule|VirtualHost|Proxy{value}")
#text = root.biuildNewConfig(4)
print(len(result))
"""