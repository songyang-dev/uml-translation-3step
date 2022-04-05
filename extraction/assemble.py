"""
Take the fragments and put them together
"""
import itertools
from typing import Tuple
from utils import uml


def assemble(fragments: list[uml.UML]):
    """
    Simple greedy algorithm
    """
    # first fragment is accepted as is
    model_in_progress = fragments[0]

    # trivial case
    if len(fragments == 1):
        return model_in_progress

    # re-order the fragments to start with classes
    incoming_classes = []
    incoming_rels = []
    for fragment in fragments:
        if fragment.classes[0].kind:
            incoming_classes.append(fragment)
        else:
            incoming_rels.append(fragment)
    fragments = incoming_classes + incoming_rels

    for incoming_fragment in fragments[1:]:

        # class fragment
        if len(incoming_fragment.classes == 1):
            incoming_class = incoming_fragment.classes[0]

            # check for existing similarities

            # direct match
            existing_class = None
            existing_class_index = -1
            for index, m in enumerate(model_in_progress.classes):
                if m.name == incoming_class.name:
                    existing_class = m
                    existing_class_index = index
            if existing_class is not None:

                merged_attributes = merge_attributes(incoming_class, existing_class)

                existing_class.attributes = merged_attributes
                model_in_progress.classes[existing_class_index] = existing_class

            # indirect match
            result = indirect_matching_class(model_in_progress, incoming_class)
            if result is not None:

                # perform merging
                model_in_progress = result
                continue

            # no match
            model_in_progress.classes.append(incoming_class)

        # rel fragment
        # TODO
        else:

            if len(incoming_fragment.classes[0].associations) != 0:
                incoming_rel = incoming_fragment.classes[0].associations[0]
            else:
                incoming_rel = incoming_fragment.classes[1].associations[0]

            # check for existing rel

            # perfect match
            # TODO: Optimize using the class names
            if incoming_rel in list(
                itertools.chain(
                    *[uml_class.associations for uml_class in model_in_progress.classes]
                )
            ):
                continue

            # indirect match

            result = most_similar_to_rel(model_in_progress, incoming_rel)
            if result is not None:
                # TODO
                pass


def merge_attributes(incoming_class, existing_class):
    # Merge attributes
    merged_attributes: list[Tuple[str, str]] = []
    for incoming_attr in incoming_class.attributes:
        existing_attr = None
        for name, existing_type in existing_class.attributes:
            if name == incoming_attr[0]:
                existing_attr = (name, existing_attr)

                # attribute not in existing class
        if existing_attr is None:
            merged_attributes.append(incoming_attr)

            # attribute collision
        else:
            # if types collide, take the existing type
            if existing_attr[1] != None:
                merged_attributes.append(existing_attr)
                # no type assigned to the existing attr, take the incoming type
            else:
                merged_attributes.append(incoming_attr)
    return merged_attributes

    # no match
    # TODO: Instantiate new classes and relationships


def indirect_matching_class(model: uml.UML, prospective_class: uml.UMLClass):
    """
    Checks for the most similar things in the model. If nothing, return None.
    """
    # Case 1: The model contains an attribute similar to the class.
    # Remove the attribute from the model and create a new relationship to the class

    # find all attributes that are identical to the prospective class
    for existing_class in model.classes:
        for attribute in existing_class.attributes:
            name, _ = attribute

            # there is an identical attribute
            if name.lower() == prospective_class.name.lower():
                # TODO
                pass

    # Case 2: The model contains a relationship *identical* to the class.
    # Introduce the prospective class as a new class, leaving the rest untouched
    return None  # The default action in assemble() will take care of it

    # Case 3: Cases 1 and 2 happen together
    # Do both


def most_similar_to_rel(model: uml.UML, prospective_rel: uml.UMLClass):
    """
    Checks for the most similar things in the model with respect to the rel. If nothing, return None.
    """
    # TODO
    pass
