"""
Generates models/robot.xml : chassis (your STLs) + 4 geared DC motors + 4 mecanum wheels.
Edit the PARAMETERS block, run `python3 make_robot.py`, then `python3 view.py` or `python3 drive_demo.py`.

Frame convention (chassis body): origin = lower-plate corner, +x = robot forward, +y = left, +z = up.
Motor axes run along y, so wheels sit at the two long (y) ends of the plate: y<0 = right side, y>175 mm = left side.
All lengths below are in metres.
"""
import math, pathlib

# ----------------------------- PARAMETERS -----------------------------------
PLATE_Y        = 0.175          # lower/upper plate depth (y)
X_WHEELS       = (0.045, 0.165) # x of rear / front wheel axes
AXIS_Z         = -0.0143        # motor axis height relative to plate underside (bore centre of the holder)
HOLDER_Y0      = 0.010          # holder occupies y = 0.010..0.040 on the right side (mirrored on the left)

# Motor (12 V geared DC, 37 mm gearbox, centre shaft) -- sizes are approximations of your photo
GEARBOX_R, GEARBOX_Y   = 0.0185, (0.008, 0.035)   # gearbox cylinder (clamped by the holder)
CAN_R,     CAN_Y       = 0.014,  (0.035, 0.080)   # motor can, pointing inboard
SHAFT_R,   SHAFT_END_Y = 0.003,  -0.052           # 6 mm shaft sticking out past the plate edge
MOTOR_NOLOAD_RPM = 200.0
MOTOR_STALL_TORQUE = 0.6        # N*m at the wheel shaft  <-- PUT YOUR DATASHEET VALUE HERE

# Mecanum wheel
WHEEL_R        = 0.040          # outer radius (80 mm wheel)  <-- change to your wheel
WHEEL_HALF_W   = 0.020          # half the wheel width
HUB_Y          = -0.032         # wheel centre y for the right side (mirrored for the left)
N_ROLLERS      = 10
ROLLER_R       = 0.010          # roller radius at its widest
ROLLER_ANGLE   = 45.0           # deg between roller axis and wheel axis
HAND = {"fl": -1, "fr": +1, "rl": +1, "rr": -1}     # roller handedness per wheel (X pattern)
MU_FLOOR       = 1.0
# -----------------------------------------------------------------------------

W_NL   = MOTOR_NOLOAD_RPM * 2 * math.pi / 60.0
KV     = MOTOR_STALL_TORQUE / W_NL
CHASSIS_Z0 = -(AXIS_Z - WHEEL_R) + 0.004     # spawn height: wheel bottom 4 mm above floor
RC = WHEEL_R - ROLLER_R                      # radius of the roller-centre circle
ROLLER_HALF_L = WHEEL_HALF_W / math.sin(math.radians(ROLLER_ANGLE)) * 0.95 / 1.0
ROLLER_HALF_L = min(ROLLER_HALF_L, 0.030)

def f(v): return f"{v:.5f}"

def roller_xml(i, hand, prefix):
    phi = 2 * math.pi * i / N_ROLLERS
    px, pz = RC * math.cos(phi), RC * math.sin(phi)
    tx, tz = -math.sin(phi), math.cos(phi)                 # tangent in the x-z plane
    a = math.radians(ROLLER_ANGLE)
    ax = (math.cos(a) * tx, hand * math.sin(a), math.cos(a) * tz)
    return (f'        <body name="{prefix}_r{i}" pos="{f(px)} 0 {f(pz)}">\n'
            f'          <joint name="{prefix}_r{i}_j" type="hinge" axis="{f(ax[0])} {f(ax[1])} {f(ax[2])}" damping="1e-5" armature="1e-6"/>\n'
            f'          <geom class="roller" size="{ROLLER_R} {ROLLER_R} {f(ROLLER_HALF_L)}" zaxis="{f(ax[0])} {f(ax[1])} {f(ax[2])}"/>\n'
            f'        </body>\n')

def wheel_xml(name, x, y):
    h = HAND[name]
    s = f'      <body name="wheel_{name}" pos="{f(x)} {f(y)} {f(AXIS_Z)}">\n'
    s += f'        <joint name="wheel_{name}_j" type="hinge" axis="0 1 0" damping="1e-4"/>\n'
    s += f'        <geom class="visual" type="cylinder" fromto="0 -0.012 0 0 0.012 0" size="0.016" mass="0.04" rgba="0.2 0.2 0.2 1"/>\n'
    for i in range(N_ROLLERS):
        s += roller_xml(i, h, f"wheel_{name}")
    s += '      </body>\n'
    return s

def motor_xml(name, x, mirror):
    """gearbox + can + shaft, drawn along y. mirror=True puts it on the left (y>PLATE_Y)."""
    def Y(v): return PLATE_Y - v if mirror else v
    z = AXIS_Z
    return (f'      <geom class="visual" name="gearbox_{name}" type="cylinder" fromto="{f(x)} {f(Y(GEARBOX_Y[0]))} {f(z)} {f(x)} {f(Y(GEARBOX_Y[1]))} {f(z)}" size="{GEARBOX_R}" mass="0.10" rgba="0.93 0.9 0.6 1"/>\n'
            f'      <geom class="visual" name="can_{name}" type="cylinder" fromto="{f(x)} {f(Y(CAN_Y[0]))} {f(z)} {f(x)} {f(Y(CAN_Y[1]))} {f(z)}" size="{CAN_R}" mass="0.12" rgba="0.7 0.7 0.72 1"/>\n'
            f'      <geom class="visual" name="shaft_{name}" type="cylinder" fromto="{f(x)} {f(Y(GEARBOX_Y[0]))} {f(z)} {f(x)} {f(Y(SHAFT_END_Y))} {f(z)}" size="{SHAFT_R}" mass="0.005" rgba="0.8 0.8 0.85 1"/>\n')

# wheel table: name -> (x, right/left)
wheels = {"rl": (X_WHEELS[0], False), "rr": (X_WHEELS[0], True),   # right side has y<0 ...
          "fl": (X_WHEELS[1], False), "fr": (X_WHEELS[1], True)}
# NOTE: 'left' wheels are the ones at y>PLATE_Y.  Naming: fl/rl on the LEFT (y>0), fr/rr on the RIGHT (y<0)
side_left = {"fl": True, "rl": True, "fr": False, "rr": False}
xpos      = {"fl": X_WHEELS[1], "fr": X_WHEELS[1], "rl": X_WHEELS[0], "rr": X_WHEELS[0]}

holders = ""
motors  = ""
wheels_xml = ""
acts = ""
for n in ("fl", "fr", "rl", "rr"):
    left = side_left[n]; x = xpos[n]
    if left:   # mirrored copy: rotate 180 deg about y
        holders += f'      <geom class="part" name="holder_{n}" mesh="motor_holder" pos="{f(x)} {f(PLATE_Y - HOLDER_Y0 - 0.030)} 0" euler="0 180 0" rgba="0.9 0.5 0.2 1"/>\n'
    else:      # flipped about x so feet touch the plate underside; flip maps y -> -y
        holders += f'      <geom class="part" name="holder_{n}" mesh="motor_holder" pos="{f(x)} {f(HOLDER_Y0 + 0.030)} 0" euler="180 0 0" rgba="0.9 0.5 0.2 1"/>\n'
    motors += motor_xml(n, x, left)
    y_hub = PLATE_Y - HUB_Y if left else HUB_Y
    wheels_xml += wheel_xml(n, x, y_hub)
    acts += (f'    <velocity name="motor_{n}" joint="wheel_{n}_j" kv="{KV:.5f}" '
             f'ctrlrange="{-W_NL:.3f} {W_NL:.3f}" forcerange="{-MOTOR_STALL_TORQUE} {MOTOR_STALL_TORQUE}"/>\n')

xml = f'''<mujoco model="mecanum_robot">
  <!-- GENERATED by make_robot.py -- edit the parameters there, not this file. Meshes are mm -> scale 0.001 -->
  <compiler angle="degree" meshdir="meshes" autolimits="true"/>
  <option timestep="0.001" gravity="0 0 -9.81" integrator="implicitfast" cone="elliptic" impratio="10"/>

  <default>
    <default class="part">
      <!-- chassis geoms: collide with the floor only -->
      <geom type="mesh" density="1240" rgba="0.75 0.75 0.78 1" contype="2" conaffinity="0"/>
    </default>
    <default class="visual">
      <geom contype="0" conaffinity="0" group="1"/>
    </default>
    <default class="roller">
      <geom type="ellipsoid" mass="0.012" rgba="0.15 0.15 0.15 1" contype="4" conaffinity="0"
            friction="{MU_FLOOR} 0.005 0.0001" condim="3"/>
    </default>
  </default>

  <asset>
    <mesh name="lower_base"   file="lower_base.stl"   scale="0.001 0.001 0.001"/>
    <mesh name="upper_base"   file="upper_base.stl"   scale="0.001 0.001 0.001"/>
    <mesh name="bar_link"     file="bar_link.stl"     scale="0.001 0.001 0.001"/>
    <mesh name="motor_holder" file="motor_holder.stl" scale="0.001 0.001 0.001"/>
    <texture type="skybox" builtin="gradient" rgb1="0.6 0.7 0.9" rgb2="0.1 0.1 0.2" width="256" height="256"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.25 0.27 0.3" rgb2="0.2 0.22 0.25" width="300" height="300"/>
    <material name="grid" texture="grid" texrepeat="8 8" reflectance="0.05"/>
  </asset>

  <worldbody>
    <light pos="0 0 2" dir="0 0 -1" diffuse="0.8 0.8 0.8"/>
    <geom name="floor" type="plane" size="5 5 0.05" material="grid" contype="1" conaffinity="6" friction="{MU_FLOOR} 0.005 0.0001"/>

    <body name="chassis" pos="0 0 {CHASSIS_Z0:.4f}">
      <freejoint name="chassis_free"/>
      <geom class="part" name="lower_base" mesh="lower_base" rgba="0.3 0.5 0.8 1"/>
      <geom class="part" name="bar_fl" mesh="bar_link" pos="0.015 0.015 0.010" rgba="0.8 0.8 0.8 1"/>
      <geom class="part" name="bar_fr" mesh="bar_link" pos="0.195 0.015 0.010" rgba="0.8 0.8 0.8 1"/>
      <geom class="part" name="bar_bl" mesh="bar_link" pos="0.015 0.160 0.010" rgba="0.8 0.8 0.8 1"/>
      <geom class="part" name="bar_br" mesh="bar_link" pos="0.195 0.160 0.010" rgba="0.8 0.8 0.8 1"/>
      <geom class="part" name="upper_base" mesh="upper_base" pos="0 0 0.085" rgba="0.3 0.7 0.5 1"/>
      <site name="robot_center" pos="0.105 0.0875 0" size="0.004"/>

      <!-- motor holders (under the plate) -->
{holders}
      <!-- geared motors (visual + mass only) -->
{motors}
      <!-- mecanum wheels: hub on a hinge about y, rollers on hinges at 45 deg -->
{wheels_xml}    </body>
  </worldbody>

  <actuator>
    <!-- velocity servo = DC-motor-like: torque = kv*(cmd - w), capped at stall torque -->
{acts}  </actuator>
</mujoco>
'''
out = pathlib.Path(__file__).parent / "models" / "robot.xml"
out.write_text(xml)
print("wrote", out, f"(kv={KV:.4f}, w_noload={W_NL:.2f} rad/s, spawn z={CHASSIS_Z0:.4f})")
