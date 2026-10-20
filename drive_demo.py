"""
Drive the mecanum robot in MuJoCo.

    python3 drive_demo.py          # interactive: click the viewer window, then use keys
    python3 drive_demo.py --auto   # scripted demo: forward, strafe, rotate, circle

Keys (latch the command; SPACE stops):
    W / S   forward / backward          A / D   strafe left / right
    Q / E   rotate left (CCW) / right   SPACE   stop
    + / -   increase / decrease speed
"""
import sys, time, pathlib
import numpy as np
import mujoco, mujoco.viewer

WHEEL_R = 0.040                                  # must match make_robot.py
HAND = {"fl": -1, "fr": +1, "rl": +1, "rr": -1}  # must match make_robot.py
NAMES = ["fl", "fr", "rl", "rr"]

model = mujoco.MjModel.from_xml_path(str(pathlib.Path(__file__).parent / "models" / "robot.xml"))
data = mujoco.MjData(model)

# wheel centres relative to the middle of the wheel rectangle (read from the model)
wpos = {n: model.body_pos[model.body(f"wheel_{n}").id][:2].copy() for n in NAMES}
centre = np.mean([wpos[n] for n in NAMES], axis=0)
rel = {n: wpos[n] - centre for n in NAMES}
act = {n: model.actuator(f"motor_{n}").id for n in NAMES}
W_MAX = model.actuator_ctrlrange[act["fl"], 1]   # motor no-load speed (rad/s)


def wheel_speeds(vx, vy, wz):
    """Body twist (m/s, m/s, rad/s) -> wheel angular speeds (rad/s). x fwd, y left, wz CCW."""
    w = np.array([(vx + HAND[n] * vy + (-rel[n][1] + HAND[n] * rel[n][0]) * wz) / WHEEL_R for n in NAMES])
    peak = np.abs(w).max()
    return w * (W_MAX / peak) if peak > W_MAX else w     # keep the ratio if a motor would saturate


def command(vx, vy, wz):
    for n, w in zip(NAMES, wheel_speeds(vx, vy, wz)):
        data.ctrl[act[n]] = w


def main():
    auto = "--auto" in sys.argv
    speed = {"v": 0.4, "w": 2.0}
    state = {"cmd": (0.0, 0.0, 0.0)}

    def on_key(keycode):
        k = chr(keycode).upper() if 0 <= keycode < 256 else ""
        v, w = speed["v"], speed["w"]
        table = {"W": (v, 0, 0), "S": (-v, 0, 0), "A": (0, v, 0), "D": (0, -v, 0),
                 "Q": (0, 0, w), "E": (0, 0, -w), " ": (0, 0, 0)}
        if k in table:
            state["cmd"] = table[k]
        elif k in ("+", "="):
            speed["v"] = min(speed["v"] * 1.25, 0.8)
        elif k in ("-", "_"):
            speed["v"] = max(speed["v"] / 1.25, 0.05)

    script = [(0, 0, 0, 1.0), (0.4, 0, 0, 2.0), (0, 0.4, 0, 2.0), (0, -0.4, 0, 2.0), (-0.4, 0, 0, 2.0),
              (0, 0, 2.0, 2.0), (0.3, 0, 1.0, 5.0), (0, 0, 0, 1.0)]

    with mujoco.viewer.launch_passive(model, data, key_callback=None if auto else on_key) as viewer:
        t_start = time.time()
        seg_end = 0.0
        seg = 0
        while viewer.is_running():
            step_t = time.time()
            if auto:
                t = data.time
                if seg < len(script) and t >= seg_end:
                    state["cmd"] = script[seg][:3]
                    seg_end += script[seg][3]
                    seg += 1
                elif seg >= len(script) and t >= seg_end:
                    seg, seg_end = 0, t
            command(*state["cmd"])
            for _ in range(16):                      # 16 physics steps (16 ms) per rendered frame
                mujoco.mj_step(model, data)
            viewer.sync()
            sleep = 16 * model.opt.timestep - (time.time() - step_t)
            if sleep > 0:
                time.sleep(sleep)


if __name__ == "__main__":
    main()
