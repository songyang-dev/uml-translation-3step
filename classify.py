# Classifies the data

import sys
if len(sys.argv) != 2:
    print("Usage: py classify.py data-file", file=sys.stderr)
    exit(1)

import pandas as pd
df = pd.read_csv(sys.argv[1])

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(df["english"], df["kind"], test_size=0.2)

def train(vectorizer: str, model: str):
    global X_train, y_train

    # vectorize using simple statistics

    if vectorizer == "count":
        from sklearn.feature_extraction.text import CountVectorizer
        vec = CountVectorizer().fit(X_train)

    elif vectorizer == "tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer().fit(X_train)
    
    else:
        raise Exception("Vectorizer unknown:{}".format(vectorizer))

    X_train = vec.transform(X_train)


    # train the model
    if model == "bayes":
        from sklearn.naive_bayes import BernoulliNB
        trained_model = BernoulliNB().fit(X_train, y_train)

    return vec, trained_model

def test(vec, trained_model):
    global X_test, y_test

    pred = trained_model.predict(vec.transform(X_test))

    from sklearn.metrics import classification_report
    print(classification_report(y_test, pred))

    return pd.DataFrame(data={"english": X_test, "truth": y_test, "prediction": pred})

vec, trained_model = train("tfidf", "bayes")
print(test(vec, trained_model))
