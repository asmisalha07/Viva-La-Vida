"""LSTM on a short window of MediaPipe hand poses (location-invariant)."""

from tensorflow.keras import Model
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam

SEQ_LEN = 12


def build_landmark_lstm(seq_len=SEQ_LEN, feat_dim=88, num_classes=26):
    """Bidirectional LSTM over recent landmark frames — better than a single-pose MLP."""
    hidden = 128 if num_classes > 15 else 64
    inp = Input(shape=(seq_len, feat_dim))
    x = Bidirectional(LSTM(hidden, return_sequences=True))(inp)
    x = Dropout(0.35)(x)
    x = LSTM(hidden)(x)
    x = Dropout(0.35)(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.25)(x)
    out = Dense(num_classes, activation="softmax")(x)
    model = Model(inp, out)
    model.compile(
        optimizer=Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def build_landmark_mlp(input_dim=63, num_classes=8):
    """Kept for older saved .keras files that were trained as a dense net."""
    from tensorflow.keras import Sequential

    hidden = 256 if num_classes > 15 else 128
    model = Sequential(
        [
            Input(shape=(input_dim,)),
            Dense(hidden, activation="relu"),
            Dropout(0.35),
            Dense(128, activation="relu"),
            Dropout(0.25),
            Dense(num_classes, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model
