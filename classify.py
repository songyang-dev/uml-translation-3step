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
    if model == "bernoulliNB":
        from sklearn.naive_bayes import BernoulliNB
        trained_model = BernoulliNB()

    elif model == "multinomialNB":
        from sklearn.naive_bayes import MultinomialNB
        trained_model = MultinomialNB()

    elif model == "knn":
        from sklearn.neighbors import KNeighborsClassifier
        trained_model = KNeighborsClassifier(3)

    elif model == "linearSVC":
        from sklearn.svm import LinearSVC
        trained_model = LinearSVC(C=0.025)

    elif model == "svc":
        from sklearn.svm import SVC
        trained_model = SVC(gamma=2, C=1)

    elif model == "gaussian":
        from sklearn.gaussian_process import GaussianProcessClassifier
        trained_model = GaussianProcessClassifier()

    elif model == "ada":
        from sklearn.ensemble import AdaBoostClassifier
        trained_model = AdaBoostClassifier()

    elif model == "forest":
        from sklearn.ensemble import RandomForestClassifier
        trained_model = RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1)

    elif model == "logistic":
        from sklearn.linear_model import LogisticRegression
        trained_model = LogisticRegression()

    else:
        raise Exception("Model unknown")

    return vec, trained_model.fit(X_train, y_train)

def test(vec, trained_model):
    global X_test, y_test

    pred = trained_model.predict(vec.transform(X_test))

    from sklearn.metrics import classification_report
    print(classification_report(y_test, pred))

    return pd.DataFrame(data={"english": X_test, "truth": y_test, "prediction": pred})

vec, trained_model = train("tfidf", "bernoulliNB")
test(vec, trained_model)

import pickle
pickle.dump(trained_model, open("model.pickle", "wb"))
pickle.dump(vec, open("model.vec", "wb"))

# print(test(vec, trained_model))

# Performances:
#   Model                   Tf-idf  Count
#   -------------------------------------
#   Bernoulli Bayes         87      83
#   Multinomial Bayes       83      85
#   k neighbours            82      74
#   Linear SVC              88      84
#   SVC                     88      55
#   Gaussian                --      --
#   ADA                     85      85
#   Random Forest           81      70
#   Logistic Regression     86      85-95