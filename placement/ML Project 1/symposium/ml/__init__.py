"""ML package.

Every syllabus algorithm has a home here:

- ``stance_svm``           -> Support Vector Machine (classification)
- ``topic_naive_bayes``    -> Naive Bayes (classification)
- ``agreement_regressor``  -> Linear + Logistic Regression
- ``similar_turn_knn``     -> K-Nearest Neighbours
- ``clustering``           -> K-Means + PCA
- ``neural_debate_scorer`` -> Keras/TensorFlow Neural Network

Import each module DIRECTLY (not via ``from symposium.ml import ...``)
so we don't force-load TensorFlow on lightweight callers.
Examples::

    from symposium.ml.stance_svm import StanceSVM
    from symposium.ml.neural_debate_scorer import NeuralDebateScorer

All models expose a common shape::

    class SomeModel:
        def train(self, X, y) -> dict[str, float]     # returns metrics
        def predict(self, X) -> np.ndarray
        def save(self, path: Path) -> None
        def load(self, path: Path) -> None
"""
