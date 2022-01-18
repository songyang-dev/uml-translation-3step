# Evaluate saved models

import os
import sys
import pickle

if len(sys.argv) != 2:
    print("Usage: py predict_kind.py text-to-classify-typed", file=sys.stderr)
    print("Example: py predict_kind.py \"The school has seven departments.\"", file=sys.stderr)
    exit(1)

# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.linear_model import LogisticRegression

path = os.path.abspath(os.path.dirname(__file__))

model = pickle.load(open(os.path.join(path, "bernoulliNB.pickle"), "rb"))
vec = pickle.load(open(os.path.join(path, "tfidf.vec"), "rb"))

print(model.predict(vec.transform([sys.argv[1]])))
