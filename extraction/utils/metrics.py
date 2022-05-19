"""
Metrics for evaluating the similarity between uml models
"""

"""
Terminology

(metrics)

Precision = true positives / (true positives + false positives)

Recall = true positives / (true positives + false negatives)

F1 = 2 (Precision x Recall) / (Precision + Recall)

(between models)

Perfect match: 
Everything is identical. All classes are found in the prediction and no
additional classes are present. All relationships are present and no
extra relationships are there.

Imperfect match:
Almost everything is identical. The number of classes and relationships
are the same, but their content is slightly off.

Poor match:
There are missing or extra classes. There are missing or extra relationships.
The entire model is still similar enough to the ground truth.

Mismatch:
There is no obvious indication that the two models are talking about the
same thing.

(between classes)

Perfect match:
Everything is identical. The names are the same. The attributes are the same.

Imperfect match:
Almost everything is identical. The names differ slightly. The attributes
have slightly difference in name or type.

Poor match:
Names may be the same, but the attributes are very different. The prediction
might have too many attributes or too little.

Mismatch:
There is no way to determine if the prediction is related to the ground truth.

(between relationships)

Perfect match:
Everything is identical. The names are the same. The multiplicity is the same.
The source and destination classes are the same.

Imperfect match:
Almost everything is good. The names and multiplicity are slightly different.
The source and destination classes are the same.

Poor match:
One of the source and destination classes is different. Names are similar.
Multiplicity is similar.

Mismatch:
Different source and destination classes.


What is positive and what is negative?

Let us consider "=" as an exact match operator and "~=" a relaxed match operator. 
Suppose "a" is an element in the expect model and "a'" an element in the generated model. 
If a'=a is true then we have a true positive. If a'=a is false and we consider the relaxed 
match, then if a'~=a is true, we consider that we have a true positive.

"""

"""
Alternative evaluation

Percent similarity score
"""
from typing import Tuple
from . import uml

import networkx
import numpy

import math


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def compute_metrics(predictions: list[uml.UML], ground_truth: list[uml.UML]):

    if len(predictions) != len(ground_truth):
        raise Exception("Disagreement in length")

    if len(predictions) == 0 or len(ground_truth) == 0:
        raise Exception("Empty lists to compare")

    return (
        [
            get_model_metrics_classes(pred, ground)
            for pred, ground in zip(predictions, ground_truth)
        ],
        [
            get_model_metrics_rels(pred, ground)
            for pred, ground in zip(predictions, ground_truth)
        ],
    )


def get_model_metrics_classes(prediction: uml.UML, ground: uml.UML):
    """
    Compute the metrics for the model with regards to classes
    """
    # the null result
    if prediction.package_name == "Nothing":
        return (0, 0, 0)

    check_model_integrity(prediction)
    check_model_integrity(ground)

    precision = 0
    recall = 0
    f1_score = 0

    def compare_classes_exactly(prediction: uml.UMLClass, ground: uml.UMLClass):
        """
        Two classes are the same if everything they contain is identical, except for the relationships
        """
        if prediction.name != ground.name:
            return False

        if len(prediction.attributes) != len(ground.attributes):
            return False

        for pred_attribute, ground_attribute in zip(
            prediction.attributes, ground.attributes
        ):
            if pred_attribute != ground_attribute:
                return False

        return True

    def compare_classes_name_only(prediction: uml.UMLClass, ground: uml.UMLClass):
        """
        Two classes are the same if the names are the same
        """
        return prediction.name == ground.name

    def compare_classes_no_type(prediction: uml.UMLClass, ground: uml.UMLClass):

        if prediction.name != ground.name:
            return False

        if len(prediction.attributes) != len(ground.attributes):
            return False

        for pred_attribute, ground_attribute in zip(
            prediction.attributes, ground.attributes
        ):
            if pred_attribute[0] != ground_attribute[0]:
                return False

        return True

    def class_comparison(prediction, ground):
        """
        Change this to the function you need
        """
        return compare_classes_name_only(prediction, ground)

    # precision: how many things in the prediction is actually correct
    # shortcoming: does not take into account duplicate classes, but that shouldn't be possible
    for pred_class in prediction.classes:
        for ground_class in ground.classes:

            if class_comparison(pred_class, ground_class):
                # two classes are identical => true positive
                precision += 1
                continue  # only one pair possible
            else:
                pass
    precision = precision / len(prediction.classes)

    # recall: how many things in the ground truth are found in the prediction
    for ground_class in ground.classes:
        for pred_class in prediction.classes:

            if class_comparison(pred_class, ground_class):
                # identical
                recall += 1
                continue  # once per ground truth class
            else:
                pass
    recall = recall / len(ground.classes)

    try:
        f1_score = 2 * (precision * recall) / (precision + recall)
    except ZeroDivisionError:
        f1_score = 0

    return (precision, recall, f1_score)


def get_model_metrics_rels(prediction: uml.UML, ground: uml.UML):
    """
    Compute the metrics for the model with regards to rels
    """
    # the null result
    if prediction.package_name == "Nothing":
        return (0, 0, 0)

    check_model_integrity(prediction)
    check_model_integrity(ground)

    precision = 0
    recall = 0
    f1_score = 0

    def compare_rels_exactly(
        prediction: Tuple[str, str, str, str], ground: Tuple[str, str, str, str]
    ):
        """
        Args are (source class name, dest class name, rel name, multiplicity)
        """
        return prediction == ground

    def compare_rels_relaxed(
        prediction: Tuple[str, str, str, str], ground: Tuple[str, str, str, str]
    ):

        return prediction[:2] == ground[:2]

    # gather all relations into a list
    predicted_relations = []
    for pred_class in prediction.classes:

        for pred_rel in pred_class.associations:
            predicted_relations.append(
                (pred_class.name, pred_rel[0].name, pred_rel[2], pred_rel[1])
            )

    ground_relations = []
    for ground_class in ground.classes:

        for ground_rel in ground_class.associations:
            ground_relations.append(
                (ground_class.name, ground_rel[0].name, ground_rel[2], ground_rel[1])
            )

    def piecewise_comparison(
        precision, recall, compare_rels_exactly, predicted_relations, ground_relations
    ):
        for predicted_rel in predicted_relations:
            for ground_rel in ground_relations:
                if compare_rels_exactly(predicted_rel, ground_rel):
                    precision += 1
                    continue
                else:
                    pass
        try:
            precision = precision / len(predicted_relations)
        except ZeroDivisionError:
            if len(ground_relations) != 0:
                precision = 0
            else:
                precision = 1

        for ground_rel in ground_relations:
            for predicted_rel in predicted_relations:
                if compare_rels_exactly(predicted_rel, ground_rel):
                    recall += 1
                    continue
                else:
                    pass
        try:
            recall = recall / len(ground_relations)
        except ZeroDivisionError:
            if len(ground_relations) != 0:
                recall = 0
            else:
                recall = 1
        return precision, recall

    def general_comparison(precision: float, recall: float):
        """
        Compares the relations without considering class names.

        1. Create two simple undirected graphs from the predicted relations and ground relations.
        2. If the number of nodes are different, add new nodes that connect to everything
        until both graph have the same number of nodes.
        3. Calculate the Laplacian matrix of the graph.
        4. Calculate the eigenvalues of the Laplacian.
        5. Compute the eigenvector similarity, defined here https://stackoverflow.com/questions/12122021/python-implementation-of-a-graph-similarity-grading-algorithm
        """

        """
        Alternatively, consider implemented features on
        https://networkx.org/documentation/stable/reference/algorithms/similarity.html
        """

        predicted_graph = prediction.get_graph_object()
        ground_graph = ground.get_graph_object()

        def select_k(spectrum, minimum_energy=0.9):
            running_total = 0.0
            total = sum(spectrum)
            if total == 0.0:
                return len(spectrum)
            for i in range(len(spectrum)):
                running_total += spectrum[i]
                if running_total / total >= minimum_energy:
                    return i + 1
            return len(spectrum)

        # array of eigenvalues
        laplacian1 = networkx.spectrum.normalized_laplacian_spectrum(predicted_graph)
        laplacian2 = networkx.spectrum.normalized_laplacian_spectrum(ground_graph)

        laplacian1 = sorted(laplacian1, reverse=True)
        laplacian2 = sorted(laplacian2, reverse=True)

        k1 = select_k(laplacian1)
        k2 = select_k(laplacian2)
        k = min(k1, k2)

        # create normalized vectors
        normalized_eigenvalues_1 = numpy.array(laplacian1[:k])
        normalized_eigenvalues_2 = numpy.array(laplacian2[:k])

        # map the norm from positive reals to [0,1] interval
        # score = -2 * sigmoid(x) + 2
        # clamp the numbers
        similarity = (
            -2
            * sigmoid(
                numpy.linalg.norm(normalized_eigenvalues_1 - normalized_eigenvalues_2)
            )
            + 2
        )
        similarity = numpy.clip(similarity, 0, 1)

        # similarity is just one half of the score
        size_difference = 0
        prediction_quantities = numpy.array(
            [predicted_graph.number_of_nodes(), predicted_graph.number_of_edges()]
        )
        ground_quantities = numpy.array(
            [ground_graph.number_of_nodes(), ground_graph.number_of_edges()]
        )
        prediction_quantities = prediction_quantities / numpy.linalg.norm(
            prediction_quantities
        )
        ground_quantities = ground_quantities / numpy.linalg.norm(ground_quantities)

        size_difference = 1 - numpy.linalg.norm(
            prediction_quantities - ground_quantities
        )

        if str(similarity) == "nan":
            raise Exception("Similarity is nan")

        if str(size_difference) == "nan":
            raise Exception("Size difference is nan")

        return similarity, size_difference

    precision, recall = piecewise_comparison(
        precision, recall, compare_rels_exactly, predicted_relations, ground_relations
    )

    # precision, recall = general_comparison(precision, recall)

    try:
        f1_score = 2 * (precision * recall) / (precision + recall)
    except ZeroDivisionError:
        f1_score = 0

    return (precision, recall, f1_score)


def check_model_integrity(model: uml.UML):
    """
    Checks for uml inconsistencies such as class duplicates
    """

    # duplicate classes
    running_up = []
    for uml_class in model.classes:
        if uml_class.name in running_up:
            raise Exception(
                "Model contains duplicate classes: {}".format(uml_class.name)
            )
        else:
            running_up.append(uml_class.name)

        # duplicate relations

        rels_running_up = []
        for rel in uml_class.associations:
            hashed = f"{rel[0].name} {rel[1]} {rel[2]}"

            if hashed in rels_running_up:
                raise Exception("Model contains duplicate relations: {}".format(hashed))
            else:
                rels_running_up.append(hashed)


if __name__ == "__main__":
    from . import inquire
    from ..assemble import remove_duplicates

    original = inquire.get_json_uml_fragment(
        r"C:\Users\songy\Documents\My Documents\UDEM\master thesis\uml data\database\analysis\three-step\extraction\temp\assembly\CFG_original_failed.json"
    )
    prediction = inquire.get_json_uml_fragment(
        r"C:\Users\songy\Documents\My Documents\UDEM\master thesis\uml data\database\analysis\three-step\extraction\temp\assembly\CFG_prediction_failed.json"
    )

    original = remove_duplicates(original)
    prediction = remove_duplicates(prediction)

    print(get_model_metrics_rels(prediction, original))
