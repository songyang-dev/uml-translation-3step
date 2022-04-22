"""
Utility script for probing into the fragment dataset
"""

import json
import os
import subprocess
from sys import argv, stdout

import pandas
from pyecore.resources import ResourceSet
from pyecore.utils import dispatch
import pyecore.ecore as ecore


if __name__ == "__main__":
    import uml

else:
    from . import uml

SOURCE_DIR = "C:\\Users\\songy\\Documents\\My Documents\\UDEM\\master thesis\\uml data\\database\\cleaning\\"

fragments_csv = os.path.join(SOURCE_DIR, "fragments.csv")
labels_csv = os.path.join(SOURCE_DIR, "labels.csv")
models_csv = os.path.join(SOURCE_DIR, "models.csv")

FRAGMENTS = pandas.read_csv(fragments_csv)
LABELS = pandas.read_csv(labels_csv)
MODELS = pandas.read_csv(models_csv)

PLANTUML_PARSER = os.path.join(
    SOURCE_DIR, "three-step", "extraction", "plantuml-parser.js"
)

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
        if o.eClass.name == "EEnum":
            return
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
        self.current_element: uml.UMLClass
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
        self.association = (
            ref.eContainer().name,
            ref.eType.name,
            f"{ref.lower}..{'*' if ref.many else ref.upper}",
            ref.name,
        )

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

            source_eclass.association(
                dest_eclass, self.association[2], self.association[3]
            )


def get_ecore_uml_fragment(label_id: int):
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
        os.path.join(SOURCE_DIR, "zoo", fragment_name)
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


def get_json_uml_fragment(label_id: int):
    # Get fragment unique id
    label = LABELS.loc[LABELS["id"] == label_id]
    fragment_id = label["fragment_id"].values[0]

    fragment = FRAGMENTS.loc[FRAGMENTS["unique_id"] == fragment_id]

    global CURRENT_FRAGMENT

    fragment_name = "{}_{}{}.json".format(
        fragment["model"].values[0],
        fragment["kind"].values[0],
        fragment["number"].values[0],
    )

    CURRENT_FRAGMENT = fragment_name

    json_file = os.path.join(SOURCE_DIR, "zoo", fragment_name)
    if not os.path.isfile(json_file):
        # parse the plantuml with the node package
        exit_code = subprocess.call(
            args=[
                "node",
                PLANTUML_PARSER,
                json_file.removesuffix(".json") + ".plantuml",
            ]
        )

        if exit_code != 0:
            raise Warning("Did not generate json properly: {}", json_file)

    return get_json_uml(json_file)


def get_ecore_uml_model(name: str):
    """
    Builds the model from the ecore uml
    """
    # UML Ecore
    rset = ResourceSet()
    metamodel_resource = rset.get_resource(
        os.path.join(SOURCE_DIR, "zoo", name + ".ecore")
    )
    root = metamodel_resource.contents[0]
    switch = PlantUMLSwitch()
    switch.generate(root)
    switch.completion()

    return switch.result


def get_uml_fragment_name(label_id: int):
    # Get fragment unique id
    label = LABELS.loc[LABELS["id"] == label_id]
    fragment_id = label["fragment_id"].values[0]

    fragment = FRAGMENTS.loc[FRAGMENTS["unique_id"] == fragment_id]

    fragment_name = "{}_{}{}".format(
        fragment["model"].values[0],
        fragment["kind"].values[0],
        fragment["number"].values[0],
    )
    return fragment_name


def get_json_uml(filename: str):
    with open(filename, "rb") as json_path:
        json_object = json.load(json_path)

    # plantuml-parser syntax
    # get the uml package
    package_level = json_object["elements"][0]

    package_name = package_level["name"]

    # uml
    model_read = uml.UML(package_name)

    package_elements = package_level["elements"]

    package_relations = []

    for element in package_elements:
        if "name" in element:
            # this is a class
            class_fragment = uml.UMLClass(element["name"], "class")

            # attributes
            if len(element["members"]) != 0:
                for member in element["members"]:
                    class_fragment.attribute(member["name"], member["type"])

            model_read.classes.append(class_fragment)

        else:
            # this is a relationship
            package_relations.append(element)

    for relation in package_relations:
        # zoo format

        # source class
        try:
            source_class = [
                eclass
                for eclass in model_read.classes
                if eclass.name == relation["left"]
            ].pop()
        except IndexError:
            # create the class
            source_class = uml.UMLClass(relation["left"], "class")
            model_read.classes.append(source_class)

        # destination class
        try:
            dest_class = [
                eclass
                for eclass in model_read.classes
                if eclass.name == relation["right"]
            ].pop()
        except IndexError:
            # create the class
            dest_class = uml.UMLClass(relation["right"], "class")
            model_read.classes.append(dest_class)

        # cardinality and name
        split_cardinality: list[str] = relation["leftCardinality"].split()
        if relation["leftCardinality"] == "":
            cardinality, name = "", ""

        elif len(split_cardinality) == 1:
            if split_cardinality[0].isalpha():
                cardinality = ""
                name = split_cardinality[0]
            else:
                cardinality = split_cardinality[0]
                name = ""

        elif len(split_cardinality) != 2:
            raise Warning(
                "Unexpected cardinality, {}".format(relation["leftCardinality"])
            )
        else:
            name, cardinality = split_cardinality

        source_class.association(dest_class, cardinality, name)

    return model_read


if __name__ == "__main__":

    model = get_json_uml("temp/cfg/CFG.json")
    model._to_plantuml(stdout)
