# Script to build a UML model with pyecore

from pyecore.ecore import EClass, EAttribute, EReference, EString, EPackage, EInt
from pyecore.resources import ResourceSet, URI

def declare_class(name):
    return EClass(name)

def attach_attribute(name: str, of: EClass, etype):
    of.eStructuralFeatures.append(EAttribute(name, etype))

def attach_relation(name: str, root: EClass, leaf: EClass):
    root.eStructuralFeatures.append(EReference(name, leaf))

def package_up(elements: list[EClass], name: str):
    # Add all the concepts to an EPackage
    my_ecore_schema = EPackage(name, nsURI='http://myecore/1.0', nsPrefix='myecore')
    my_ecore_schema.eClassifiers.extend(elements)
    return my_ecore_schema

def save_package(my_ecore_schema, path: str):
    rset = ResourceSet()
    resource = rset.create_resource(URI(path))  # This will create an XMI resource
    resource.append(my_ecore_schema)  # we add the EPackage instance in the resource
    resource.save()  # we then serialize it