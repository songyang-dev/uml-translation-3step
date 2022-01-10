# Python module to represent UML for our purposes

# FEATURES
# Class with attributes, but no methods
# Simple associations between classes including multiplicity and names

from io import TextIOWrapper
from typing import List, Tuple


class UMLClass:

    def __init__(self, name: str, kind: str) -> None:
        self.name = name
        self.attributes : List[Tuple[str, str]] = []
        self.associations : List[Tuple["UMLClass", str, str]] = []
        self.kind = kind

    def attribute(self, name: str, attribute_type: str):
        self.attributes.append((name, attribute_type))
        return self

    def association(self, destination: "UMLClass", multiplicity="", name="") -> None:
        # multiplicity can be
        # "1..1": one to one
        # "0..1": zero or one
        # "0..*": zero or many
        # "1..*": one or many
        # "": none
        self.associations.append((destination, multiplicity, name))

    def _to_plantuml(self, file_object: TextIOWrapper):
        print(f"class {self.name}", file=file_object)
        
        if self.kind == "class":
            self._class_to_plantuml(file_object)

        elif self.kind == "association":
            self._associations_to_plantuml(file_object)
        
        else:
            self._class_to_plantuml(file_object)
            self._associations_to_plantuml(file_object)

    def _associations_to_plantuml(self, file_object):
        for association in self.associations:
            destination, multiplicity, name = association

            if multiplicity == "1..1":
                association = f"{self.name} \"1\" --> \"1\" {destination}"
            elif multiplicity == "0..1":
                association = f"{self.name} \"0\" --> \"1\" {destination}"
            elif multiplicity == "0..*":
                association = f"{self.name} \"0\" --> \"*\" {destination}"
            elif multiplicity == "1..*":
                association = f"{self.name} \"1\" --> \"*\" {destination}"
            else:
                association = f"{self.name} --> {destination}"
                
            if name != "":
                association += f" : {name}"
                
            print(association, file=file_object)

    def _class_to_plantuml(self, file_object):
        print("{", file=file_object)
        for attribute in self.attributes:
            print(f"{attribute[0]} : {attribute[1]}", file=file_object)
        print("}", file=file_object)

    def __str__(self) -> str:
        return self.name

class UML:
    def __init__(self, package_name: str) -> None:
        self.package_name = package_name
        self.classes : List[UMLClass] = []
    
    def umlclass(self, umlclass: UMLClass):
        self.classes.append(umlclass)
        return self

    def save(self, path: str):
        
        file_object = open(path, "w")
        self._to_plantuml(file_object)
        file_object.close()

        return self

    # https://plantuml.com/class-diagram
    def _to_plantuml(self, file_object: TextIOWrapper):
        
        print("@startuml", file=file_object)
        print("!theme plain", file=file_object)
        for c in self.classes:
            c._to_plantuml(file_object=file_object)
        print("@enduml", file=file_object)