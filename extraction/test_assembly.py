import shutil
from utils import inquire, uml
import assemble

import os, pandas

# Initialize the test suite
CURRENT_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ZOO_DIR = "C:\\Users\\songy\\Documents\\My Documents\\UDEM\\master thesis\\uml data\\database\\cleaning\\zoo\\"
SOURCE_DIR = "C:\\Users\\songy\\Documents\\My Documents\\UDEM\\master thesis\\uml data\\database\\cleaning\\"

TEMP_FOLDER = os.path.join(CURRENT_SCRIPT_DIR, "temp")
os.makedirs(TEMP_FOLDER, exist_ok=True)

LABELS = pandas.read_csv(os.path.join(SOURCE_DIR, "labels.csv"))
FRAGMENTS = pandas.read_csv(os.path.join(SOURCE_DIR, "fragments.csv"))


def test_assembly():
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
        model = inquire.get_uml_model(model_name)
        models[model_name] = model

        # get the fragment's uml
        label_id: str = row["id"]
        fragment_uml = inquire.get_uml_fragment(int(label_id))
        if model_name in grouped:
            grouped[model_name].append(fragment_uml)
        else:
            grouped[model_name] = [fragment_uml]

    # Apply the algorithm to groups of fragments
    assembled_models: dict[str, uml.UML] = {}
    for model_name, fragments in grouped.items():
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

    if len(assembled_models) != len(models):
        raise Exception("There are different amounts of assembled models than models.")

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


if __name__ == "__main__":
    test_assembly()
