import os
import glob
import joblib
import pandas as pd
import ocr_utils
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

TRAINING_DIR = "training_data"
CATEGORIES = ["Invoice", "Purchase Order", "Resume", "Policy", "Claim", "Other"]


def extract_text(filepath: str) -> str:
    # PDFs are OCR'd page-by-page (see ocr_utils.py) so training-time
    # extraction matches what happens to live uploads in app.py.
    if filepath.lower().endswith(".pdf"):
        return ocr_utils.ocr_pdf_path(filepath)
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_dataset() -> pd.DataFrame:
    rows = []
    for category in CATEGORIES:
        folder = os.path.join(TRAINING_DIR, category)
        files = glob.glob(os.path.join(folder, "*.pdf")) + glob.glob(os.path.join(folder, "*.txt"))
        print(f"{category}: found {len(files)} files")
        for fp in files:
            text = extract_text(fp)
            if text.strip():
                rows.append({"text": text, "category": category})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_dataset()
    print(f"\nTotal training documents: {len(df)}")
    print(df["category"].value_counts(), "\n")

    le = LabelEncoder()
    y = le.fit_transform(df["category"])

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=len(CATEGORIES),
        eval_metric="mlogloss",
        n_jobs=-1,
    )
    model.fit(X_train_vec, y_train)

    preds = model.predict(X_test_vec)
    print(classification_report(le.inverse_transform(y_test), le.inverse_transform(preds)))

    joblib.dump({"vectorizer": vectorizer, "model": model, "label_encoder": le}, "model.pkl")
    print("Saved vectorizer + XGBoost model + label encoder to model.pkl")
