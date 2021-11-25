# 3Step formula for the translation of English to UML
The algorithm has three steps, starting with an English text.

## 0 Pre-processing
The input data needs to be segmented into many fragments, usually by sentences.

## 1 Classification
The English parts are each classified into either 'class' or 'relationship'.
* class: The English text is describing a class and its attributes.
* relationship: The English text is describing the relationship between two classes.

## 2 Syntax parsing
The English is parsed into syntax trees. Using a part-of-speech heuristic, we populate a UML fragment. The kind of fragment was determined by the previous step's classification.

## 3 Assembly
All UML fragments are assembled back to one large UML model, mainting logical consistency. This UML model is the final translation in UML.