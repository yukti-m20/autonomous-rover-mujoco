import mujoco, mujoco.viewer, pathlib
model = mujoco.MjModel.from_xml_path(str(pathlib.Path(__file__).parent / "models" / "robot.xml"))
data = mujoco.MjData(model)
mujoco.viewer.launch(model, data)
