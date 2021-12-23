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
        self.kind = kind

    def attribute(self, name: str, attribute_type: str):
        self.attributes.append((name, attribute_type))
        return self

    def association(self, destination: "UMLClass", multiplicity="1..1", name="") -> None:
        # multiplicity can be
        # "1..1": one to one
        # "0..1": zero or one
        # "0..*": zero or many
        # "1..*": one or many
        self.destination = destination
        self.multiplicity = multiplicity
        self.association_name = name

    def _to_plantuml(self, file_object: TextIOWrapper):
        print(f"class {self.name}", file=file_object)
        
        if self.kind == "class":
            print("{", file=file_object)
            for attribute in self.attributes:
                print(f"{attribute[0]} : {attribute[1]}", file=file_object)
            print("}", file=file_object)

        else:
            if self.multiplicity == "1..1":
                association = f"{self.name} \"1\" --> \"1\" {self.destination}"
            elif self.multiplicity == "0..1":
                association = f"{self.name} \"0\" --> \"1\" {self.destination}"
            elif self.multiplicity == "0..*":
                association = f"{self.name} \"0\" --> \"*\" {self.destination}"
            elif self.multiplicity == "1..*":
                association = f"{self.name} \"1\" --> \"*\" {self.destination}"
            
            if self.association_name != "":
                association += f" : {self.association_name}"
            
            print(association, file=file_object)

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