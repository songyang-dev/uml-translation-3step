# 3Step formula for the translation of English to UML

The algorithm has three steps, starting with an English text. Described in this paper: https://arxiv.org/abs/2210.14441 

## Installation

To run this repo, you need Python 3 and several Python modules. All can be installed via `pip`. A `requirements.txt` file is provided so you can `pip install -r requirements.txt`.

- numpy
- pandas
- scikit-learn
- spacy, then download its small English model
- pyecore
- termcolor
- coreferee, and then install the English model
  - This will also install Tensorflow and keras.

Anaconda or the mini version is recommended.

In addition, a UML visualization tool is required. Built in Java.

- plantuml, for visualization

## 0 Pre-processing

The input data needs to be segmented into many fragments, usually by sentences. The dataset has been segmented into fragments already. We do not segment large text here.

Scripts involved:

- `preprocess.py`: Prepares the data into a `csv` file for easy reading in further steps.

## 1 Classification

The English parts are each classified into either 'class' or 'relationship'.

- class: The English text is describing a class and its attributes.
- relationship: The English text is describing the relationship between two classes.

The best model is a Tf-idf vectorized Bernoulli classifier, at around 90%!

Scripts involved:

- `preprocess.py`: Prepares the data ready for reading into a `pandas` DataFrame and for classification with `scikit-learn`.
- `classify.py`: Trains and saves a scikit-learn statistical model. The models are not neural.
- `predict_kind.py`: A command-line tool to predict the kind of English sentence given in stdin, using the best model (Bernoulli) trained so far. This is for qualitative evaluation purposes.

## 2 Syntax parsing

The English is parsed into syntax trees. Using a part-of-speech and dependency heuristic, we populate a UML fragment. The kind of fragment was determined by the previous step's classification.

Scripts involved:

- `parse.py`: Parses the English text using Spacy
- `ecore.py`: Provides an interface to the PyEcore library to build UML
- `ecore2plant.py`: Third-party script that coverts an `.ecore` file to a `.plantuml` file
- `sentence2fragment.sh`: Script that streamlines the entire parsing pipeline to produce `.ecore` files, `.plantuml` files and images

## 3 Assembly

All UML fragments are assembled back to one large UML model, maintaining logical consistency. This UML model is the final translation in UML.

The assembly (also called composition) algorithm is a greedy algorithm that combines UML fragments one at a time into a work-in-progress larger model. The details of the algorithm are described in the paper.
