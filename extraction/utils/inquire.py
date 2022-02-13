"""
Utility script for probing into the fragment dataset
"""

import os
from sys import argv

import pandas
from pyecore.resources import ResourceSet
from pyecore.utils import dispatch
import pyecore.ecore as ecore


if __name__ == "__main__":
    import uml
    if len(argv) != 3:
        print("Usage: py inquire.py dir_where_the_data_is label_id")
        exit(1)
    source_dir = argv[1]
    label_id = argv[2]

else:
    from . import uml
    source_dir = "C:\\Users\\songy\\Documents\\My Documents\\UDEM\\master thesis\\uml data\\database\\cleaning\\"

fragments_csv = os.path.join(source_dir, "fragments.csv")
labels_csv = os.path.join(source_dir, "labels.csv")
models_csv = os.path.join(source_dir, "models.csv")

FRAGMENTS = pandas.read_csv(fragments_csv)
LABELS = pandas.read_csv(labels_csv)
MODELS = pandas.read_csv(models_csv)

CURRENT_FRAGMENT = None

class PlantUMLSwitch(object):
    def __init__(self):
        self.visited = set()
        self.result = None
        self.current_element = None
        self.association = None

    @dispatch
    def generate(self, o):
        self.current_element = o
        print("Object kind unsupported", o.eClass.name)

    @generate.register(ecore.EPackage)
    def epackage_switch(self, p):

        self.result = uml.UML(p.name)
        for classif in p.eClassifiers:
            self.generate(classif)

    @generate.register(ecore.EClass)
    def eclass_switch(self, o):
        
        self.current_element = uml.UMLClass(o.name, "rel")
        self.result.classes.append(self.current_element)

        for attrib in o.eAttributes:
            self.generate(attrib)

        for ref in o.eReferences:
            
            self.generate(ref)

    @generate.register(ecore.EAttribute)
    def eattribute_switch(self, a):
        self.current_element : uml.UMLClass
        self.current_element.attribute(a.name, a.eType.name)

    @generate.register(ecore.EReference)
    def ereference_switch(self, ref):
        if ref in self.visited:
            return
        self.visited.add(ref)

        # multiplicity
        label = f"{ref.name} {ref.lower}..{'*' if ref.many else ref.upper}"
        link = "--"
        if ref.containment:
            link = "*" + link
        
        link += ">"
        self.association = (ref.eContainer().name, ref.eType.name, f"{ref.lower}..{'*' if ref.many else ref.upper}", ref.name)

    # @generate.register(ecore.EDataType)
    # def edatatype_switch(self, o):
    #     print("class", o.name, "<< (D,orchid) EDataType>>")

    def completion(self):
        if self.association is not None:
            source_name = self.association[0]
            dest_name = self.association[1]

            if self.result.classes[0].name == source_name:
                source_eclass = self.result.classes[0]
                dest_eclass = self.result.classes[1]
            else:
                source_eclass = self.result.classes[1]
                dest_eclass = self.result.classes[0]
            
            source_eclass.association(dest_eclass, self.association[2], self.association[3])

def get_uml_fragment(label_id: int):
    # Get fragment unique id
    label = LABELS.loc[LABELS["id"] == label_id]
    fragment_id = label["fragment_id"].values[0]

    fragment = FRAGMENTS.loc[FRAGMENTS["unique_id"] == fragment_id]

    global CURRENT_FRAGMENT

    fragment_name = "{}_{}{}.ecore".format(
        fragment["model"].values[0],
        fragment["kind"].values[0],
        fragment["number"].values[0],
    )

    CURRENT_FRAGMENT = fragment_name

    # UML Ecore
    rset = ResourceSet()
    metamodel_resource = rset.get_resource(
        os.path.join(source_dir, "zoo", fragment_name)
    )
    root = metamodel_resource.contents[0]
    switch = PlantUMLSwitch()
    switch.generate(root)
    switch.completion()
    
    if fragment["kind"].values[0] == "class":
        switch.result.classes[0].kind = "class"
    
    if switch.result is None:
        raise Exception("No original fragment!!")
    return switch.result


if __name__ == "__main__":

    get_uml_fragment(int(label_id))
    print(CURRENT_FRAGMENT)
