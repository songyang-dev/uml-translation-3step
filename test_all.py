"""
Tests the entire pipeline using metrics
"""
from classification.predict_kind import LazyLoadedClassifier
from extraction.preprocess import resolve_coref
from extraction.parse import LazyLoadedExtractor
from extraction.assemble import assemble, remove_duplicates
from extraction.utils import uml, metrics, inquire

import os
import pandas


def setup():
    global SOURCE_DIR, ZOO_DIR
    SOURCE_DIR = os.path.join(os.path.dirname(__file__), "..")
    ZOO_DIR = os.path.join(SOURCE_DIR, "zoo")

    # load the CSV of grouped data
    global GROUPED
    try:
        GROUPED = pandas.read_csv(
            os.path.join(SOURCE_DIR, "three-step", "data", "grouped.csv")
        )
    except FileNotFoundError:
        print("group.csv does not exist. Please generate it.")
        exit(1)

    global LOG_DIR
    LOG_DIR = os.path.join(SOURCE_DIR, "three-step", "data", "logs")
    os.makedirs(LOG_DIR, exist_ok=True)


def make_predictions():
    """
    Run the pipeline. Returns the predictions.
    """

    classifier = LazyLoadedClassifier()
    class_extractor = LazyLoadedExtractor("", "class")
    rel_extractor = LazyLoadedExtractor("", "rel")

    predictions: dict[str, uml.UML] = {}

    # Read the data
    for _, row in GROUPED.iterrows():
        model_name = row["model"]
        grouped_text = row["text"]

        # preprocess each data point
        preprocessed_text = resolve_coref(grouped_text)

        # classify each sentence
        classification_results = {}
        extraction_results = []
        for index, sentence in preprocessed_text.items():
            predicted_kind = classifier.predict(sentence)
            classification_results[index] = predicted_kind

            if predicted_kind == "class":
                class_extractor.extractor.set_sentence(sentence)
                result = class_extractor.handle_class()
            elif predicted_kind == "rel":
                rel_extractor.extractor.set_sentence(sentence)
                result = rel_extractor.handle_rel()
            else:
                raise Exception("Unexpected kind!")

            extraction_results.append(result)

        # assemble the fragments
        assembly_result = assemble(extraction_results)

        predictions[model_name] = assembly_result

    return predictions


def evaluate(predictions: dict[str, uml.UML]):
    """
    Fetch ground truth and compare them
    """
    ground_truth = []
    predicted_models = []
    for model_name, prediction in predictions.items():

        ground = inquire.get_json_uml(os.path.join(ZOO_DIR, f"{model_name}.json"))
        ground_truth.append(ground)
        predicted_models.append(prediction)

    return metrics.compute_metrics(predicted_models, ground_truth)


def selective_test():
    original = inquire.get_json_uml_fragment(
        r"C:\Users\songy\Documents\My Documents\UDEM\master thesis\uml data\database\analysis\three-step\extraction\temp\assembly\CFG_original_failed.json"
    )
    prediction = inquire.get_json_uml_fragment(
        r"C:\Users\songy\Documents\My Documents\UDEM\master thesis\uml data\database\analysis\three-step\extraction\temp\assembly\CFG_prediction_failed.json"
    )

    original = remove_duplicates(original)
    prediction = remove_duplicates(prediction)

    print(metrics.compute_metrics([prediction], [original]))


if __name__ == "__main__":
    setup()
    print("Running metric based test suite. Logs are reported in {}".format(LOG_DIR))

    predictions = make_predictions()
    class_scores, rel_scores = evaluate(predictions)
    print("Class scores", class_scores)
    print("Rel scores", rel_scores)
    print("Unweighted Mean for Classes", [sum(y) / len(y) for y in zip(*class_scores)])
    print("Unweighted Mean for Relations", [sum(y) / len(y) for y in zip(*rel_scores)])
    print("(Precision, Recall, f1)")

    # selective_test()
