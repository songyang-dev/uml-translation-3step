# https://gist.github.com/aranega/eca9c8fbbd87b2f9c70317da53676ac6
# Usage
# https://github.com/pyecore/pyecore/issues/104
from pyecore.resources import ResourceSet
from pyecore.utils import dispatch
import pyecore.ecore as ecore


class PlantUMLSwitch(object):
    def __init__(self):
        self.visited = set()

    @dispatch
    def generate(self, o):
        print('Object kind unsupported', o.eClass.name)

    @generate.register(ecore.EPackage)
    def epackage_switch(self, p):
        print('package', p.name, '{')
        for classif in p.eClassifiers:
            self.generate(classif)
        print('}')

    @generate.register(ecore.EClass)
    def eclass_switch(self, o):
        kind = 'interface' if o.interface else 'class'
        print(kind, o.name, '{')
        for attrib in o.eAttributes:
            self.generate(attrib)
        print('}')
        for sclass in o.eSuperTypes:
            print(sclass.name, '<|--', o.name)
        for ref in o.eReferences:
            self.generate(ref)

    @generate.register(ecore.EAttribute)
    def eattribute_switch(self, a):
        print('\t', a.name, ':', a.eType.name)

    @generate.register(ecore.EReference)
    def ereference_switch(self, ref):
        if ref in self.visited:
            return
        self.visited.add(ref)
        label = f"{ref.name} {ref.lower}..{'*' if ref.many else ref.upper}"
        link = "--"
        if ref.containment:
            link = '*' + link
        o_label = ""
        if ref.eOpposite:
            o = ref.eOpposite
            self.visited.add(o)
            o_label = f"{o.name} {o.lower}..{'*' if o.many else o.upper}"
            if o.containment:
                link += '*'
            print(f'{ref.eContainer().name} "{label}" {link} "{o_label}" {ref.eType.name}')
        else:
            link += '>'
            print(f'{ref.eContainer().name} "{label}" {link} {ref.eType.name}')

    @generate.register(ecore.EEnum)
    def enum_switch(self, o):
        print('enum', o.name, '{')
        for literal in o.eLiterals:
            print(literal.name)
        print('}')

    @generate.register(ecore.EDataType)
    def edatatype_switch(self, o):
        print('class', o.name, '<< (D,orchid) EDataType>>')


def generate(mm):
    print('@startuml')
    print('!theme plain')
    switch = PlantUMLSwitch()
    switch.generate(mm)
    print('@enduml')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} ecore_file")
        sys.exit(1)
    rset = ResourceSet()
    metamodel_resource = rset.get_resource(sys.argv[1])
    root = metamodel_resource.contents[0]
    generate(root)
