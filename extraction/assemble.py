"""
Take the fragments and put them together
"""
from typing import Tuple
from .utils import uml


def assemble(fragments: list[uml.UML]):
    """
    Simple greedy algorithm
    """
    # first not none fragment
    try:
        model_in_progress = [f for f in fragments if f is not None][0]
    except IndexError:
        return uml.UML("Nothing")

    # trivial case
    if len(fragments) == 1:
        return model_in_progress

    # re-order the fragments to start with classes
    incoming_classes = []
    incoming_rels = []
    for fragment in fragments:
        if fragment is None:
            continue

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

    return remove_duplicates(model_in_progress)


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
    # Case 0: The model contains an existing class whose name is very close to the
    # prospective class.
    for existing_class in model.classes:

        if existing_class.name.lower() == prospective_class.name.lower():
            existing_class.attributes = merge_attributes(
                prospective_class, existing_class
            )
            return model

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


def remove_duplicates(model: uml.UML):
    """
    Removes the duplicated classes and relationships
    """
    new_model = uml.UML(model.package_name)

    new_classes: dict[str, uml.UMLClass] = {}  # name, uml
    # name (source dest), list[tuple] (tuple[0] = name, tuple[1] = mult)
    new_relationships = {}

    for uml_class in model.classes:

        if not uml_class.name in new_classes:
            new_classes[uml_class.name] = uml.UMLClass(uml_class.name, "class")
            new_classes[uml_class.name].attributes = uml_class.attributes

        else:
            # merge attributes
            for attribute in uml_class.attributes:

                if attribute not in new_classes[uml_class.name].attributes:
                    new_classes[uml_class.name].attribute(attribute[0], attribute[1])

        # relationships
        get_unique_relationships(new_relationships, uml_class)

    # link all the relationships
    for name, relation in new_relationships.items():
        source_name, dest_name = name.split()

        for relation_tuple in relation:
            new_classes[source_name].association(
                new_classes[dest_name], relation_tuple[1], relation_tuple[0]
            )

    new_model.classes = list(new_classes.values())
    return new_model


def get_unique_relationships(new_relationships, uml_class: uml.UMLClass):
    for relation in uml_class.associations:
        relation_hash = f"{uml_class.name} {relation[0].name}"

        if relation_hash in new_relationships:
            # look for names
            has_existing_name = False
            for rel in new_relationships[relation_hash]:
                if rel[0] == relation[2]:
                    has_existing_name = True

                    # if an existing relationship of the same name, merge multiplicity
                    if rel[1] == "" and relation[1] != "":
                        # multiplicity takes over no multiplicity
                        rel[1] = relation[1]
                    else:
                        # precedence is given to existing multiplicity in the case of conflicting non-null mults
                        pass
                    break

                # no existing name found, create a new one
            if not has_existing_name:
                new_relationships[relation_hash].append((relation[2], relation[1]))

        else:
            # create the hash for the source-dest case
            new_relationships[relation_hash] = [(relation[2], relation[1])]
