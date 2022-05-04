"""
Take the fragments and put them together
"""
from typing import Tuple
from .utils import uml


def assemble(fragments: list[uml.UML]):
    """
    Simple greedy algorithm
    """
    # first fragment is accepted as is
    model_in_progress = fragments[0]

    # trivial case
    if len(fragments) == 1:
        return model_in_progress

    # re-order the fragments to start with classes
    incoming_classes = []
    incoming_rels = []
    for fragment in fragments:
        if fragment.classes[0].kind == "class":
            incoming_classes.append(fragment)
        else:
            incoming_rels.append(fragment)
    fragments = incoming_classes + incoming_rels

    for incoming_fragment in fragments[1:]:

        # class fragment
        if len(incoming_fragment.classes) == 1:
            incoming_class = incoming_fragment.classes[0]

            # check for existing similarities

            # direct match
            existing_class = None
            existing_source_class_index = -1
            for index, m in enumerate(model_in_progress.classes):
                if m.name == incoming_class.name:
                    existing_class = m
                    existing_source_class_index = index
            if existing_class is not None:

                merged_attributes = merge_attributes(incoming_class, existing_class)

                existing_class.attributes = merged_attributes
                model_in_progress.classes[existing_source_class_index] = existing_class
                continue

            # indirect match
            result = indirect_matching_class(model_in_progress, incoming_class)
            if result is not None:

                # perform merging
                model_in_progress = result
                continue

            # no match
            model_in_progress.classes.append(incoming_class)
            continue

        # rel fragment
        else:

            if len(incoming_fragment.classes[0].associations) != 0:
                incoming_rel = incoming_fragment.classes[0].associations[0]
                rel_source_class_name = incoming_fragment.classes[0].name
            else:
                incoming_rel = incoming_fragment.classes[1].associations[0]
                rel_source_class_name = incoming_fragment.classes[1].name

            # check for existing classes

            # perfect match
            rel_dest_class_name = incoming_rel[0].name
            existing_source_class_index = -1
            existing_dest_class_index = -1

            for index, existing_class in enumerate(model_in_progress.classes):
                if existing_class.name == rel_source_class_name:
                    existing_source_class_index = index
                if existing_class.name == rel_dest_class_name:
                    existing_dest_class_index = index

            # one class does not exist
            if existing_dest_class_index == -1 and existing_source_class_index != -1:
                new_dest_class = uml.UMLClass(rel_dest_class_name, "class")
                model_in_progress.classes[existing_source_class_index].association(
                    new_dest_class, incoming_rel[1], incoming_rel[2]
                )
                model_in_progress.classes.append(new_dest_class)
                continue

            elif existing_dest_class_index != -1 and existing_source_class_index == -1:
                new_source_class = uml.UMLClass(rel_source_class_name, "class")
                new_source_class.association(
                    model_in_progress.classes[existing_dest_class_index],
                    incoming_rel[1],
                    incoming_rel[2],
                )
                model_in_progress.classes.append(new_source_class)
                continue

            elif existing_source_class_index != -1 and existing_dest_class_index != -1:
                # make a new rel between the two classes
                model_in_progress.classes[existing_source_class_index].association(
                    model_in_progress.classes[existing_dest_class_index],
                    incoming_rel[1],
                    incoming_rel[2],
                )
                continue

            # SHOULD BE UNREACHABLE
            # indirect match

            result = indirect_matching_rel(model_in_progress, incoming_rel)
            if result is not None:
                model_in_progress = result
                continue

            # no match
            # TODO: Instantiate new classes and relationships
            model_in_progress.classes.extend(incoming_fragment.classes)

            continue

    return model_in_progress


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


def indirect_matching_class(model: uml.UML, prospective_class: uml.UMLClass):
    """
    Checks for the most similar things in the model. If nothing, return None.

    Returns the merged model.
    """
    # Case 1: The model contains an attribute similar to the class.
    # Remove the attribute from the model and create a new relationship to the class

    # find all attributes that are identical to the prospective class
    for existing_class in model.classes:
        found_attribute = False

        new_attributes = existing_class.attributes.copy()

        for attribute in existing_class.attributes:
            name, _ = attribute

            # there is an identical attribute
            if name.lower() == prospective_class.name.lower():
                new_attributes.remove(attribute)
                found_attribute = True

        # this existing class contains an identical attribute
        if found_attribute:
            existing_class.attributes = new_attributes

            association_name = prospective_class.name
            association_name = association_name[0].lower() + association_name[1:]

            # create new rel to the new class
            existing_class.association(prospective_class, "", association_name)

    model.classes.append(prospective_class)

    # Case 2: The model contains a relationship *identical* to the class.
    # Introduce the prospective class as a new class, leaving the rest untouched
    # return None  # The default action in assemble() will take care of it

    # Case 3: Cases 1 and 2 happen together
    # Do both
    return model


def indirect_matching_rel(model: uml.UML, prospective_rel: uml.UMLClass):
    """
    Checks for the most similar things in the model with respect to the rel. If nothing, return None.

    Returns the merged model.
    """
    # TODO
    # Do nothing for now
    return None
