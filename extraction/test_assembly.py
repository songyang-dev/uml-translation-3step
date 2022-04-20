import pickle
import re
import shutil
from utils import inquire, uml
import assemble
from parse import LazyLoadedExtractor
from preprocess import resolve_coref, LazyLoadedClassifier

import os, pandas

# Initialize the test suite
CURRENT_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ZOO_DIR = "C:\\Users\\songy\\Documents\\My Documents\\UDEM\\master thesis\\uml data\\database\\cleaning\\zoo\\"
SOURCE_DIR = "C:\\Users\\songy\\Documents\\My Documents\\UDEM\\master thesis\\uml data\\database\\cleaning\\"

TEMP_FOLDER = os.path.join(CURRENT_SCRIPT_DIR, "temp")
os.makedirs(TEMP_FOLDER, exist_ok=True)

LABELS = pandas.read_csv(os.path.join(SOURCE_DIR, "labels.csv"))
FRAGMENTS = pandas.read_csv(os.path.join(SOURCE_DIR, "fragments.csv"))


PICKLED_DIR = os.path.join(TEMP_FOLDER, "pickled")
os.makedirs(PICKLED_DIR, exist_ok=True)
PREPROCESSED_PICKLED_DIR = os.path.join(PICKLED_DIR, "preprocessed")
os.makedirs(PREPROCESSED_PICKLED_DIR, exist_ok=True)


def test_assembly_ground_truth():
    """
    Checks the assembly algorithm using the dataset's original fragments and models.

    The fragments are ground truth. The models are ground truth.
    """

    # Read the ground truth fragments from the dataset

    # Group the fragments according to their models
    models: dict[str, uml.UML] = {}
    grouped: dict[str, list[uml.UML]] = {}

    for index, row in LABELS.iterrows():

        fragment = FRAGMENTS.loc[FRAGMENTS["unique_id"] == row["fragment_id"]]

        # get the model's uml
        model_name = fragment["model"].values[0]
        # selective runs
        if model_name != "CFG":
            continue
        model = inquire.get_ecore_uml_model(model_name)
        models[model_name] = model

        # get the fragment's uml
        label_id: str = row["id"]
        fragment_uml = inquire.get_ecore_uml_fragment(int(label_id))
        if model_name in grouped:
            grouped[model_name].append(fragment_uml)
        else:
            grouped[model_name] = [fragment_uml]

    # Apply the algorithm to groups of fragments
    assembled_models: dict[str, uml.UML] = {}
    for model_name, fragments in grouped.items():
        # # selective runs
        # if model_name != "CFG":
        #     continue
        assembled = assemble.assemble(fragments=fragments)
        assembled_models[model_name] = assembled

    # Compare the results with the ground truth model
    passed = 0
    passed_models = []
    failed = 0
    failed_models = []

    passed_predictions: list[uml.UML] = []
    failed_predictions: list[uml.UML] = []

    # print predictions and ground truths
    results_folder = os.path.join(TEMP_FOLDER, "assembly")
    os.makedirs(results_folder, exist_ok=True)
    shutil.rmtree(results_folder)
    os.makedirs(results_folder, exist_ok=True)

    # if len(assembled_models) != len(models):
    #     raise Exception("There are different amounts of assembled models than models.")

    for predicted, ground_truth in zip(assembled_models.items(), models.items()):
        model_name, prediction = predicted
        _, original = ground_truth

        if prediction == original:
            passed += 1
            passed_models.append(model_name)
            passed_predictions.append(prediction)

            prediction.save(
                os.path.join(results_folder, model_name + "_prediction_passed.plantuml")
            )
            original.save(
                os.path.join(results_folder, model_name + "_original_passed.plantuml")
            )
        else:
            failed += 1
            failed_models.append(model_name)
            failed_predictions.append(prediction)

            prediction.save(
                os.path.join(results_folder, model_name + "_prediction_failed.plantuml")
            )
            original.save(
                os.path.join(results_folder, model_name + "_original_failed.plantuml")
            )

    print("Passed", passed)
    print("Failed", failed)

    # More detailed metrics for the predictions and the models
    passed_model_class_counts = [len(model.classes) for model in passed_predictions]
    failed_model_class_counts = [len(model.classes) for model in failed_predictions]

    original_model_class_counts = []
    for prediction in failed_models:
        original_model_class_counts.append(len(models[prediction].classes))

    passed_dataframe = pandas.DataFrame(
        data={"model": passed_models, "class count": passed_model_class_counts}
    )
    failed_dataframe = pandas.DataFrame(
        data={
            "model": failed_models,
            "class count": failed_model_class_counts,
            "original class count": original_model_class_counts,
        }
    )

    passed_dataframe.to_csv(os.path.join(TEMP_FOLDER, "assembly_passed.csv"))
    failed_dataframe.to_csv(os.path.join(TEMP_FOLDER, "assembly_failed.csv"))


def run_nlp_pipeline():
    """
    Runs the NLP pipeline on classified labels to generate prediction fragments
    Save results to disk
    """
    classified_fragments_path = os.path.join(
        SOURCE_DIR, "three-step", "data", "fragment_kinds.csv"
    )
    classified_fragments = pandas.read_csv(
        classified_fragments_path, header=0, index_col=0
    )

    class_extractor = LazyLoadedExtractor("", "class")
    rel_extractor = LazyLoadedExtractor("", "rel")

    for index, row in classified_fragments.iterrows():
        if row["kind"] == "class":
            class_extractor.extractor.set_sentence(row["english"])
            result = class_extractor.handle_class(verbose=False)
        elif row["kind"] == "rel":
            rel_extractor.extractor.set_sentence(row["english"])
            result = rel_extractor.handle_rel(verbose=False)
        else:
            raise Exception("Unexpected kind!")

        if result is not None:
            # get the name of this fragment
            ground_truth_fragment_name = inquire.get_uml_fragment_name(index)
            # pickle the uml under this name
            with open(
                os.path.join(PICKLED_DIR, ground_truth_fragment_name), "wb+"
            ) as pickled_file:
                pickle.dump(result, pickled_file)


def run_nlp_pipeline_preprocessed():
    classified_fragments_path = os.path.join(
        SOURCE_DIR, "three-step", "data", "grouped.csv"
    )
    classified_fragments = pandas.read_csv(
        classified_fragments_path, header=0, index_col=0
    )

    class_extractor = LazyLoadedExtractor("", "class")
    rel_extractor = LazyLoadedExtractor("", "rel")
    classifier = LazyLoadedClassifier()

    for row_index, row in classified_fragments.iterrows():
        model_name = row["model"]

        # call preprocessor
        split_sentences = resolve_coref(row["text"])

        for index, sentence in split_sentences.items():

            # call classifier
            kind = classifier.predict(text=sentence)
            if kind == "class":
                class_extractor.extractor.set_sentence(sentence)
                result = class_extractor.handle_class(verbose=False)
            elif kind == "rel":
                rel_extractor.extractor.set_sentence(sentence)
                result = rel_extractor.handle_rel(verbose=False)
            else:
                raise Exception("Unexpected kind!")

            # save the result to disk
            if result is not None:
                # get the name of this fragment
                ground_truth_fragment_name = f"{model_name}_{kind}{index}"
                # pickle the uml under this name
                with open(
                    os.path.join(PREPROCESSED_PICKLED_DIR, ground_truth_fragment_name),
                    "wb+",
                ) as pickled_file:
                    pickle.dump(result, pickled_file)


def test_assembly(used_preprocessed: bool = False):
    """
    Tests the assembly on the fragments generated by the pipeline.

    Two choices. Raw fragments or preprocessed fragments.
    """

    # Use the NLP pipeline and save intermediary results to disk

    # Read raw fragments from the fragment_kinds.csv
    if not used_preprocessed:
        if len(os.listdir(PICKLED_DIR)) == 0:
            run_nlp_pipeline()

        grouped = read_pickles(PICKLED_DIR)

    # Read preprocessed fragments from the split.csv
    else:
        if len(os.listdir(PREPROCESSED_PICKLED_DIR)) == 0:
            run_nlp_pipeline_preprocessed()
        grouped = read_pickles(PREPROCESSED_PICKLED_DIR)

    results = {}

    for model_name, fragments in grouped.items():
        results[model_name] = assemble.assemble(fragments)

    # Compare the assembled result with ground truth, version "zoo plantuml"
    # This depends on the plantuml parser


def read_pickles(location: str):
    grouped = {}  # model name, list of fragments

    for pickled_path in os.listdir(location):
        with open(os.path.join(location, pickled_path)) as pickled_file:
            pickled: uml.UML = pickle.load(pickled_file)

        model_name = re.split("_(class|rel)\d+", pickled_path)[0]

        if model_name in grouped:
            grouped[model_name].append(pickled)
        else:
            grouped[model_name] = []
    return grouped


if __name__ == "__main__":
    run_nlp_pipeline_preprocessed()
