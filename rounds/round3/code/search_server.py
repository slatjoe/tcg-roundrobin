#!/usr/bin/env python3
"""search_server.py — inference server for the ISMCTS player (see
DESIGN.md). One process, thread-per-connection, unix socket bridge with
the same framing as rollout_server.py (4-byte BE length + JSON).

Request kinds:
  - ping (R12, round-3 rerun): {"type":"ping"}
    -> {"learner_seat":int, "model":path}. Lets the driver verify the
    server's identity before an arm and record it on every row.
  - normal decision requests (identical shape to rollout_server):
    {"v":1,"game","decision","branch","player","state","candidates",
     "gate_pass"} -> {"v":1,"action_index":int,"learner_seat":int}
    Learner seat (TCG_LEARNER_SEAT) = SEARCH_MODEL argmax (v15);
    opponent seat = TCG_OPP_MIX single policy (heuristic -> v1 argmax;
    ckptpath:<path> -> that net argmax), mirroring eval.py semantics.
  - leaf evaluation requests from search children:
    {"mode":"eval","state":{...},"candidates":[...]}
    -> {"priors":[floats], "value":float}
    Evals go through a batching dispatcher (up to EVAL_BATCH items or
    EVAL_WAIT_MS ms) so leaf evaluations from many forked children are
    served by single batched forward passes on the GPU when available.

Env:
  TCG_POLICY_SOCK  socket path (default /tmp/tcg_policy.sock)
  SEARCH_MODEL     v3 checkpoint for the searching player (required)
  TCG_OPP_MIX      e.g. "heuristic:1.0" or "ckptpath:/abs/ckpt.pt:1.0"
  TCG_LEARNER_SEAT 1|2 (required in eval use)
  EVAL_BATCH       max batch size (default 48)
  EVAL_WAIT_MS     batch wait window ms (default 3)
"""

import json
import os
import queue
import socket
import struct
import sys
import threading
import time

SOCK_PATH = os.environ.get("TCG_POLICY_SOCK", "/tmp/tcg_policy.sock")
SEARCH_MODEL = os.environ.get("SEARCH_MODEL", "")
OPP_MIX_RAW = os.environ.get("TCG_OPP_MIX", "heuristic:1.0")
LEARNER_SEAT = int(os.environ.get("TCG_LEARNER_SEAT", "1"))
EVAL_BATCH = int(os.environ.get("EVAL_BATCH", "48"))
EVAL_WAIT_S = float(os.environ.get("EVAL_WAIT_MS", "3")) / 1000.0

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import bc_features  # noqa: E402

import torch  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_num_threads(2)

import bc_features_v3  # noqa: E402
from ppo_model_v3 import PPOPolicyV3  # noqa: E402


def load_v3(path):
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    assert ckpt.get("arch") == "v3", f"{path} is not a v3 checkpoint"
    model = PPOPolicyV3(len(ckpt["vocab"]))
    model.load_state_dict(ckpt["model"], strict=True)
    model.eval().to(DEVICE)
    return model, ckpt["vocab"]


if not SEARCH_MODEL or not os.path.exists(SEARCH_MODEL):
    print(f"search_server: SEARCH_MODEL missing: {SEARCH_MODEL!r}",
          flush=True)
    sys.exit(1)
MODEL, VOCAB = load_v3(SEARCH_MODEL)
print(f"search_server: search model loaded ({SEARCH_MODEL}) on {DEVICE}",
      flush=True)

# Opponent model for normal requests (net opponents only).
OPP_MODEL, OPP_VOCAB = None, None
_opp = OPP_MIX_RAW.split(":", 1)[0] if OPP_MIX_RAW else "heuristic"
if OPP_MIX_RAW.startswith("ckptpath:"):
    _p = OPP_MIX_RAW[len("ckptpath:"):].rpartition(":")[0]
    OPP_MODEL, OPP_VOCAB = load_v3(_p)
    print(f"search_server: opp net loaded ({_p})", flush=True)
OPP_KIND = "net" if OPP_MODEL is not None else "heuristic"


def featurize(state, cands):
    sv, own, opp = bc_features_v3.featurize_state_v3(state, VOCAB)
    cf = [bc_features.featurize_candidate(c, VOCAB) for c in cands]
    return sv, own, opp, [c for c, _ in cf], [z for _, z in cf]


def forward_batch(items):
    """items: list of (state, cands). Returns list of (priors, value)."""
    B = len(items)
    K = max(1, max(len(c) for _, c in items))
    svs, owns, opps, cids, czs = [], [], [], [], []
    for state, cands in items:
        sv, own, opp, ci, zi = featurize(state, cands)
        svs.append(sv)
        owns.append(own)
        opps.append(opp)
        pad = K - len(ci)
        cids.append(ci + [0] * pad)
        czs.append(zi + [0] * pad)
    import numpy as np
    t = lambda x, dt: torch.as_tensor(np.asarray(x), dtype=dt,  # noqa: E731
                                      device=DEVICE)
    with torch.no_grad():
        logits, value = MODEL(
            t(svs, torch.float32),
            t(owns, torch.long), t(opps, torch.long),
            t(cids, torch.long), t(czs, torch.long))
    out = []
    for i, (_, cands) in enumerate(items):
        k = len(cands)
        lg = logits[i, :k].float()
        priors = torch.softmax(lg, dim=0).tolist()
        out.append((priors, max(-1.0, min(1.0, float(value[i])))))
    return out


# ------------------------------------------------------------- batching

_eval_q = queue.Queue()
_stats = {"evals": 0, "batches": 0, "normal": 0, "fallbacks": 0,
          "seat_mismatch": 0}


def dispatcher():
    while True:
        first = _eval_q.get()
        batch = [first]
        deadline = time.time() + EVAL_WAIT_S
        while len(batch) < EVAL_BATCH:
            wait = deadline - time.time()
            if wait <= 0:
                break
            try:
                batch.append(_eval_q.get(timeout=wait))
            except queue.Empty:
                break
        items = [(req["state"], req["candidates"]) for req, _ in batch]
        try:
            results = forward_batch(items)
        except Exception as e:
            print(f"search_server: batch forward failed: {e}", flush=True)
            results = [([1.0 / max(1, len(c))] * len(c), 0.0)
                       for _, c in items]
        _stats["evals"] += len(batch)
        _stats["batches"] += 1
        for (_, ev), (priors, value) in zip(batch, results):
            ev.result = (priors, value)
            ev.set()


class EvalEvent(threading.Event):
    result = None


def evaluate(state, cands):
    if not cands:
        return [], 0.0
    ev = EvalEvent()
    _eval_q.put(({"state": state, "candidates": cands}, ev))
    ev.wait()
    return ev.result


# ------------------------------------------------------------- normal reqs

def v1_argmax(req):
    if not req.get("gate_pass", False):
        return -1
    cands = req.get("candidates", []) or []
    if not cands:
        return -1
    best_i, best_s = 0, None
    for i, c in enumerate(cands):
        s = float(c.get("v1_score", 0.0))
        if best_s is None or s > best_s:
            best_s, best_i = s, i
    return best_i


def net_argmax(model, vocab, state, cands):
    import numpy as np
    sv, own, opp = bc_features_v3.featurize_state_v3(state, vocab)
    cf = [bc_features.featurize_candidate(c, vocab) for c in cands]
    tt = lambda x, dt: torch.as_tensor(np.asarray(x), dtype=dt,  # noqa: E731
                                       device=DEVICE)
    with torch.no_grad():
        logits, _v = model(
            tt([sv], torch.float32), tt([own], torch.long),
            tt([opp], torch.long),
            tt([[c for c, _ in cf]], torch.long),
            tt([[z for _, z in cf]], torch.long))
    return int(logits[0].argmax())


TRAJ_DIR = os.environ.get("TCG_TRAJ_LOG", "")
_meta_fh = None
_games_seen = set()
if TRAJ_DIR:
    os.makedirs(TRAJ_DIR, exist_ok=True)
    _meta_fh = open(os.path.join(TRAJ_DIR, "games_meta.jsonl"), "a",
                    buffering=1)


def note_game(req):
    gid = req.get("game")
    if _meta_fh is None or gid is None or gid in _games_seen:
        return
    _games_seen.add(gid)
    _meta_fh.write(json.dumps({
        "game": gid, "learner_seat": LEARNER_SEAT,
        "opp": OPP_KIND, "ts": time.time()}) + "\n")


def answer_normal(req):
    note_game(req)
    cands = req.get("candidates") or []
    if not req.get("gate_pass", False) or not cands:
        return -1
    _stats["normal"] += 1
    try:
        if int(req.get("player", 0)) == LEARNER_SEAT:
            return net_argmax(MODEL, VOCAB, req["state"], cands)
        if OPP_KIND == "net":
            return net_argmax(OPP_MODEL, OPP_VOCAB, req["state"], cands)
        return v1_argmax(req)
    except Exception:
        _stats["fallbacks"] += 1
        return v1_argmax(req)


# ------------------------------------------------------------- bridge

def read_msg(conn):
    hdr = b""
    while len(hdr) < 4:
        chunk = conn.recv(4 - len(hdr))
        if not chunk:
            return None
        hdr += chunk
    (n,) = struct.unpack(">I", hdr)
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(min(65536, n - len(buf)))
        if not chunk:
            raise ConnectionError("short read")
        buf += chunk
    return json.loads(buf.decode("utf-8"))


def write_msg(conn, obj):
    payload = json.dumps(obj).encode("utf-8")
    conn.sendall(struct.pack(">I", len(payload)) + payload)


def handle_conn(conn):
    try:
        while True:
            req = read_msg(conn)
            if req is None:
                break
            if req.get("type") == "ping":
                write_msg(conn, {"learner_seat": LEARNER_SEAT,
                                 "model": SEARCH_MODEL})
                continue
            # R12 seat routing, enforced: a request that names its
            # learner seat is rejected loudly when it names the wrong
            # one. Requests without the field (legacy callers) are
            # served as before. The error payload deliberately lacks
            # action_index/priors so both PHP clients fail the query
            # instead of playing a silently mis-seated pick.
            ls = req.get("learner_seat")
            if ls is not None and int(ls) != LEARNER_SEAT:
                _stats["seat_mismatch"] += 1
                print(f"search_server: SEAT_MISMATCH request_seat={ls} "
                      f"server_seat={LEARNER_SEAT} "
                      f"count={_stats['seat_mismatch']}", flush=True)
                write_msg(conn, {"v": 1, "error": "seat_mismatch",
                                 "learner_seat": LEARNER_SEAT})
                continue
            if req.get("mode") == "eval":
                priors, value = evaluate(req["state"],
                                         req.get("candidates") or [])
                write_msg(conn, {"priors": priors, "value": value,
                                 "learner_seat": LEARNER_SEAT})
            else:
                write_msg(conn, {"v": 1,
                                 "action_index": answer_normal(req),
                                 "learner_seat": LEARNER_SEAT})
    except (ConnectionError, json.JSONDecodeError, BrokenPipeError):
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main():
    try:
        os.unlink(SOCK_PATH)
    except FileNotFoundError:
        pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK_PATH)
    srv.listen(128)
    threading.Thread(target=dispatcher, daemon=True).start()
    print(f"search_server: listening on {SOCK_PATH} "
          f"(learner seat {LEARNER_SEAT}, opp {OPP_KIND})", flush=True)
    t0 = time.time()
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle_conn, args=(conn,),
                         daemon=True).start()
        if _stats["evals"] and int(time.time() - t0) % 30 == 0:
            pass  # (kept simple: stats printed on demand via SIGUSR1-free log)
        if _stats["batches"] % 200 == 0 and _stats["batches"]:
            dt = time.time() - t0
            print(f"search_server: evals={_stats['evals']} "
                  f"batches={_stats['batches']} normal={_stats['normal']} "
                  f"fallbacks={_stats['fallbacks']} "
                  f"seat_mismatch={_stats['seat_mismatch']} up={dt:.0f}s",
                  flush=True)


if __name__ == "__main__":
    main()
