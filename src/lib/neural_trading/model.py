"""
model.py
Pure-numpy LSTM neural network for trading signal generation.

Architecture
------------
  Input  : sequence of shape (seq_len, FEATURE_DIM=17)
  LSTM 1 : hidden_size=64
  LSTM 2 : hidden_size=32  (stacked)
  FC     : 32 → 16 → 3 (softmax)
  Output : probabilities for [SELL, HOLD, BUY]

Training
--------
  Uses synthetic war-period data to pre-train weights so the model
  arrives with sensible priors without needing a live data pipeline.
  Call  model.train(X, y)  with real labelled sequences to fine-tune.

Labels
------
  0 = SELL   (market likely to fall)
  1 = HOLD   (no strong directional edge)
  2 = BUY    (market likely to rise)
"""

import numpy as np
from .features import FEATURE_DIM, FeatureEngine

SIGNAL_LABELS = {0: "SELL", 1: "HOLD", 2: "BUY"}


# ---------------------------------------------------------------------------
# Activations
# ---------------------------------------------------------------------------
def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))

def _tanh(x):
    return np.tanh(np.clip(x, -30, 30))

def _softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()

def _relu(x):
    return np.maximum(0.0, x)


# ---------------------------------------------------------------------------
# LSTM Cell (single step)
# ---------------------------------------------------------------------------
class _LSTMCell:
    def __init__(self, input_dim: int, hidden_dim: int, seed: int = 0):
        rng   = np.random.default_rng(seed)
        scale = np.sqrt(2.0 / (input_dim + hidden_dim))
        combo = input_dim + hidden_dim
        # All four gates packed into one matrix (input, forget, cell, output)
        self.W = rng.normal(0, scale, (4 * hidden_dim, combo)).astype(np.float32)
        self.b = np.zeros(4 * hidden_dim, dtype=np.float32)
        self.b[hidden_dim:2*hidden_dim] = 1.0  # forget gate bias = 1
        self.hidden_dim = hidden_dim

    def step(self, x: np.ndarray, h: np.ndarray, c: np.ndarray):
        """x:(input_dim,)  h:(hidden_dim,)  c:(hidden_dim,)"""
        combined = np.concatenate([x, h])
        gates    = self.W @ combined + self.b
        hd       = self.hidden_dim
        i_gate   = _sigmoid(gates[0   : hd  ])
        f_gate   = _sigmoid(gates[hd  : 2*hd])
        g_gate   = _tanh   (gates[2*hd: 3*hd])
        o_gate   = _sigmoid(gates[3*hd: 4*hd])
        c_new    = f_gate * c + i_gate * g_gate
        h_new    = o_gate * _tanh(c_new)
        return h_new, c_new

    def forward_seq(self, X: np.ndarray):
        """X:(T, input_dim) → h:(T, hidden_dim)"""
        T        = X.shape[0]
        h        = np.zeros(self.hidden_dim, dtype=np.float32)
        c        = np.zeros(self.hidden_dim, dtype=np.float32)
        outputs  = np.zeros((T, self.hidden_dim), dtype=np.float32)
        for t in range(T):
            h, c       = self.step(X[t], h, c)
            outputs[t] = h
        return outputs, (h, c)


# ---------------------------------------------------------------------------
# Full Model
# ---------------------------------------------------------------------------
class TradingLSTM:
    """
    Two-layer stacked LSTM + FC head outputting [SELL, HOLD, BUY] probabilities.
    """

    def __init__(
        self,
        input_dim:   int = FEATURE_DIM,
        hidden1:     int = 64,
        hidden2:     int = 32,
        seq_len:     int = 20,   # look-back window fed to LSTM
        lr:          float = 0.005,
        seed:        int = 42,
    ):
        self.input_dim = input_dim
        self.hidden1   = hidden1
        self.hidden2   = hidden2
        self.seq_len   = seq_len
        self.lr        = lr

        rng = np.random.default_rng(seed)

        self.lstm1 = _LSTMCell(input_dim, hidden1, seed=seed)
        self.lstm2 = _LSTMCell(hidden1,   hidden2, seed=seed+1)

        # FC layers: hidden2 → 16 → 3
        self.W1 = rng.normal(0, np.sqrt(2/hidden2), (16, hidden2)).astype(np.float32)
        self.b1 = np.zeros(16, dtype=np.float32)
        self.W2 = rng.normal(0, np.sqrt(2/16),      (3,  16)).astype(np.float32)
        self.b2 = np.zeros(3,  dtype=np.float32)

        # Pre-train on synthetic data
        self._pretrain(rng)

    # ------------------------------------------------------------------
    def _forward(self, X: np.ndarray):
        """X:(seq_len, input_dim) → probs:(3,)"""
        h1, _  = self.lstm1.forward_seq(X)
        h2, _  = self.lstm2.forward_seq(h1)
        last   = h2[-1]
        fc1    = _relu(self.W1 @ last + self.b1)
        logits = self.W2 @ fc1 + self.b2
        return _softmax(logits)

    # ------------------------------------------------------------------
    def predict(self, features: np.ndarray) -> dict:
        """
        Parameters
        ----------
        features : (T, FEATURE_DIM) array from FeatureEngine.build()

        Returns
        -------
        {
          "signal":     "BUY" | "HOLD" | "SELL",
          "signal_int": 2 | 1 | 0,
          "confidence": float  (0-1),
          "probs":      {"BUY": p, "HOLD": p, "SELL": p},
        }
        """
        if len(features) < self.seq_len:
            pad   = np.zeros((self.seq_len - len(features), self.input_dim), dtype=np.float32)
            features = np.vstack([pad, features])
        seq   = features[-self.seq_len:].astype(np.float32)
        probs = self._forward(seq)
        idx   = int(np.argmax(probs))
        return {
            "signal":     SIGNAL_LABELS[idx],
            "signal_int": idx,
            "confidence": float(probs[idx]),
            "probs": {
                "SELL": float(probs[0]),
                "HOLD": float(probs[1]),
                "BUY":  float(probs[2]),
            },
        }

    # ------------------------------------------------------------------
    def train(
        self,
        X: np.ndarray,   # (N_samples, seq_len, input_dim)
        y: np.ndarray,   # (N_samples,) int labels 0/1/2
        epochs: int = 20,
        verbose: bool = True,
    ):
        """
        Lightweight SGD training loop using cross-entropy loss.
        Updates FC weights (LSTM weights kept from pre-training for stability).
        """
        N = len(X)
        for epoch in range(epochs):
            total_loss = 0.0
            correct    = 0
            idx        = np.random.permutation(N)
            for i in idx:
                probs    = self._forward(X[i])
                label    = int(y[i])
                loss     = -np.log(probs[label] + 1e-9)
                total_loss += loss

                # Gradient of cross-entropy + softmax
                dlogits       = probs.copy()
                dlogits[label] -= 1.0

                # Backprop through FC layers (simplified – no LSTM backprop)
                fc1_out   = self._last_fc1(X[i])   # shape (16,)
                h2_out    = self._last_h2(X[i])    # shape (32,)
                dW2       = np.outer(dlogits, fc1_out)
                db2       = dlogits
                dfc1      = self.W2.T @ dlogits
                dfc1_relu = dfc1 * (fc1_out > 0)
                dW1       = np.outer(dfc1_relu, h2_out)
                db1       = dfc1_relu

                self.W2 -= self.lr * dW2
                self.b2 -= self.lr * db2
                self.W1 -= self.lr * dW1
                self.b1 -= self.lr * db1

                correct += int(np.argmax(probs) == label)

            if verbose:
                acc = correct / N * 100
                avg = total_loss / N
                print(f"  Epoch {epoch+1:>2}/{epochs}  loss={avg:.4f}  acc={acc:.1f}%")

    def _last_h2(self, seq):
        h1, _ = self.lstm1.forward_seq(seq)
        h2, _ = self.lstm2.forward_seq(h1)
        return h2[-1]

    def _last_fc1(self, seq):
        h2 = self._last_h2(seq)
        return _relu(self.W1 @ h2 + self.b1)   # shape (16,)

    # ------------------------------------------------------------------
    def _pretrain(self, rng: np.random.Generator):
        """
        Generate synthetic labelled sequences and run a quick training pass
        so weights are not completely random at first use.

        Synthetic label logic:
          - High war tension (feature 14) + VIX rising (feature 8) → SELL
          - Low war tension + RSI < 0.35 + price recovering   → BUY
          - Otherwise → HOLD
        """
        N, epochs = 400, 8
        X_syn = rng.random((N, self.seq_len, self.input_dim)).astype(np.float32)
        y_syn = np.ones(N, dtype=int)   # default HOLD

        for i in range(N):
            war   = X_syn[i, -1, 14]  # war_tension last step
            vix   = X_syn[i, -1, 7]   # vix_norm last step
            rsi   = X_syn[i, -1, 3]   # rsi
            spy   = X_syn[i, -1, 0]   # spy_ret_1d

            if war > 0.55 and vix > 0.5:
                y_syn[i] = 0   # SELL
            elif war < 0.25 and rsi < 0.4 and spy > 0.5:
                y_syn[i] = 2   # BUY

        self.train(X_syn, y_syn, epochs=epochs, verbose=False)
