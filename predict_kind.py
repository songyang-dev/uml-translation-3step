# Evaluate saved models

import sys
import pickle

if len(sys.argv) != 2:
    print("Usage: py predict_kind.py text-to-classify-typed", file=sys.stderr)
    exit(1)

# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.linear_model import LogisticRegression

model = pickle.load(open("model.pickle", "rb"))
vec = pickle.load(open("model.vec", "rb"))

print(model.predict(vec.transform([sys.argv[1]])))
