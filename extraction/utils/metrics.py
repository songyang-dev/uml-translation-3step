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
from . import uml


def compute_metrics(predictions: list[uml.UML], ground_truth: list[uml.UML]):

    if len(predictions) != len(ground_truth):
        raise Exception("Disagreement in length")

    if len(predictions) == 0 or len(ground_truth) == 0:
        raise Exception("Empty lists to compare")

    return [
        get_model_metrics_classes(pred, ground)
        for pred, ground in zip(predictions, ground_truth)
    ]


def get_model_metrics_classes(prediction: uml.UML, ground: uml.UML):
    """
    Compute the metrics for the model with regards to classes
    """
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

    # precision: how many things in the prediction is actually correct
    # shortcoming: does not take into account duplicate classes, but that shouldn't be possible
    for pred_class in prediction.classes:
        for ground_class in ground.classes:

            if compare_classes_exactly(pred_class, ground_class):
                # two classes are identical => true positive
                precision += 1
                continue  # only one pair possible
            else:
                pass
    precision = precision / len(prediction.classes)

    # recall: how many things in the ground truth are found in the prediction
    for ground_class in ground.classes:
        for pred_class in prediction.classes:

            if compare_classes_exactly(pred_class, ground_class):
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


if __name__ == "__main__":
    import inquire

    original = inquire.get_json_uml_fragment(
        r"C:\Users\songy\Documents\My Documents\UDEM\master thesis\uml data\database\analysis\three-step\extraction\temp\assembly\CFG_original_failed.json"
    )
    prediction = inquire.get_json_uml_fragment(
        r"C:\Users\songy\Documents\My Documents\UDEM\master thesis\uml data\database\analysis\three-step\extraction\temp\assembly\CFG_prediction_failed.json"
    )

    print(get_model_metrics_classes(prediction, original))
