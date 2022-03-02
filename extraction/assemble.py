"""
Take the fragments and put them together
"""
from .utils import uml


def assemble(fragments: list[uml.UML]):
    uml_classes: list[uml.UMLClass] = []

    for fragment in fragments:
        for eclass in fragment.classes:
            if eclass in uml_classes:
                continue
            uml_classes.append(eclass)

    result = uml.UML(uml_classes[0].name)
    result.classes = uml_classes
    return result
