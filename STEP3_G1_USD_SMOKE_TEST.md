# STEP 3: G1 USD Smoke Test & Validation Guide

**Step 3 of GR00T integration: Validate and visualize converted G1 (23-DOF) USD model in Isaac Sim, checking physics properties and basic functionality.**

## 🎯 Objective

Load the converted G1 USD file into Isaac Sim, verify physics properties, and confirm the robot displays and behaves correctly with basic physics simulation.

## 📋 Prerequisites ✅

- **✅ STEP 1**: Isaac Sim 5.0.0 installed and working
- **✅ STEP 2**: G1 URDF converted to USD successfully
- **✅ USD File Location**: `/home/pedro_setubal/Workspaces/unitree_rl/IsaacLab/source/extensions/omni.isaac.lab_assets/data/Robots/Unitree/G1/23dof/g1_23dof.usd`

## 🚀 Smoke Test Checklist

### A. Open Isaac Sim and Instantiate USD (2-3 min) 🔄

**Important**: Converting creates USD files, but doesn't automatically load them into a scene. We need to manually instantiate the robot.

**COMMAND FOR USER TO EXECUTE:**
```bash
# Activate environment and launch Isaac Sim UI
source ~/anaconda3/etc/profile.d/conda.sh
conda activate unitree-groot
export OMNI_KIT_ACCEPT_EULA=YES

# Launch Isaac Sim with clean UI (no ROS2 bridge)
isaacsim isaacsim.exp.full --reset-user --/exts/isaacsim.ros2.bridge/enabled=false
```

**Manual Steps in Isaac Sim UI:**

1. **Open Content Browser**: `Windows` → `Content`

2. **Navigate to USD file**:
   - Browse to: `IsaacLab/source/extensions/omni.isaac.lab_assets/data/Robots/Unitree/G1/23dof/`
   - Locate: `g1_23dof.usd`

3. **Instantiate Robot**:
   - **Drag** `g1_23dof.usd` from Content Browser to the **Stage**
   - Should create a `Xform` with `ArticulationRoot` inside

4. **Add Ground Plane**:
   - `Create` → `Physics` → `Ground Plane`

5. **Position Robot**:
   - Select G1 in Stage tree
   - In Properties panel, set Position Z to `0.02` (2cm above ground)

6. **Test Physics**:
   - Click **Play** button
   - G1 should respond to gravity naturally (stand or fall without exploding)

### Alternative: Python Script Method

If UI dragging doesn't work, use this script in Isaac Sim Python Script Editor:

```python
from omni.isaac.core.utils.prims import create_prim
from pxr import Usd, UsdGeom, Sdf
import omni.usd
from omni.isaac.core.utils.stage import add_ground_plane

stage = omni.usd.get_context().get_stage()

# Add Ground Plane
add_ground_plane(prim_path="/World/GroundPlane", size=10.0)

# Load G1 USD
g1_path = "file:///home/pedro_setubal/Workspaces/unitree_rl/IsaacLab/source/extensions/omni.isaac.lab_assets/data/Robots/Unitree/G1/23dof/g1_23dof.usd"
ref = UsdGeom.Xform.Define(stage, Sdf.Path("/World/G1"))
ref.GetPrim().GetReferences().AddReference(g1_path)

# Elevate 2cm above ground
xform = UsdGeom.Xformable(stage.GetPrimAtPath("/World/G1"))
xform.AddTranslateOp().Set((0.0, 0.0, 0.02))

print("G1 robot loaded successfully!")
```

### B. Troubleshooting: If Robot Doesn't Appear (1-2 min) 🔧

**Check these common issues:**

- [ ] **UI vs Headless**: Ensure you ran `exp.full` (UI), not streaming headless
- [ ] **Stage Tree**: G1 should be visible in Outliner/Stage as `/World/G1`
- [ ] **File Path**: Verify USD path is correct and file exists
- [ ] **Scale**: Check viewport scale - robot should be ~1.7m tall
- [ ] **Layer**: Ensure USD loaded in active layer
- [ ] **Ground Position**: Robot positioned above ground (z > 0)

### C. Apply Foot Friction Material (30 sec) 🦶

**Prevent foot slipping during physics tests:**

1. **Select Foot Links** in Stage tree (left/right ankle/foot links)
2. **Create Physics Material**: Right-click → `Create` → `Physics` → `Physics Material`
3. **Configure Friction**:
   - Name: `G1_Foot_Material`
   - Static Friction: `1.0`
   - Dynamic Friction: `0.8` 
   - Restitution: `0.1`
4. **Apply Material** to foot collision meshes

### D. Physics Properties Validation (1-2 min) ⚖️

**Verify URDF properties were preserved in USD:**

**Select ArticulationRoot** and inspect in Properties panel:

- [ ] **Joint Limits**: Position/velocity limits from URDF
- [ ] **Mass/Inertia**: Each link shows correct mass and inertia tensor  
- [ ] **Joint Drives**: Stiffness=100.0, damping=1.0 (from conversion)
- [ ] **DOF Count**: 23 degrees of freedom total
- [ ] **Collision**: Convex hull colliders present

**Key Joints to Check:**
- Hip joints (x3 per leg)
- Knee joints  
- Ankle joints (x2 per leg)
- Shoulder/elbow joints

### E. Save Scene and Complete (30 sec) 💾

1. **Test Complete**: Press Play, observe natural physics response
2. **Save Scene**: `File` → `Save As` → `g1_smoke_test.usd`
3. **Document Results**: Note any issues or successes
4. **Close Isaac Sim**

---

## ✅ Success Criteria

**This step is complete when:**

- [ ] **✅ G1 Robot Visible**: Robot appears correctly in Isaac Sim viewport
- [ ] **✅ Physics Response**: Robot responds naturally to gravity (no explosions)
- [ ] **✅ Joint Properties**: 23 DOF with correct limits and drives
- [ ] **✅ Collision**: Robot interacts properly with ground plane
- [ ] **✅ Materials**: Foot friction prevents unrealistic sliding

---

## 🚨 Common Issues & Solutions

### Issue: Robot Doesn't Appear
**Cause**: USD not instantiated in scene  
**Solution**: Use drag-and-drop from Content Browser or Python script method

### Issue: Robot Falls Through Ground  
**Cause**: No collision or incorrect positioning  
**Solution**: Add ground plane and position robot at z=0.02

### Issue: Robot "Explodes" on Play
**Cause**: Joint limits or collision issues  
**Solution**: Check joint stiffness/damping values, reduce if needed

### Issue: Viewport Shows Nothing
**Cause**: Camera position or scale issues  
**Solution**: Use `F` key to frame robot, check viewport scale

---

## 🎯 What Comes Next

**After successful smoke test:**

### STEP 4: Isaac Lab WASD Teleoperation
- Load G1 USD in Isaac Lab framework
- Implement keyboard WASD controls
- Test basic locomotion commands

### STEP 5: GR00T Integration  
- Connect GR00T N1.5 as policy backend
- Map WASD inputs to GR00T locomotion behaviors
- Full walking validation

---

## 🔗 Reference Links

- **URDF Source**: [Unitree G1 23-DOF Official](https://github.com/unitreerobotics/unitree_ros)
- **Isaac Sim URDF Import**: [Tutorial Documentation](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/robot_setup/import_urdf.html)
- **Isaac Lab Asset Import**: [How-to Guide](https://isaac-sim.github.io/IsaacLab/v1.4.0/source/how-to/import_new_asset.html)

---

**Status**: ✅ **SMOKE TEST COMPLETED SUCCESSFULLY!**

## 🎊 **VALIDATION RESULTS - AUGUST 14, 2025**

### ✅ **All Tests PASSED:**
- **✅ Isaac Sim UI**: Opened successfully without crashes
- **✅ USD Loading**: G1 robot imported correctly via Content Browser drag-and-drop
- **✅ Ground Plane**: Added successfully, robot positioned at z=0.02
- **✅ Physics Simulation**: Robot responded naturally to gravity on Play
- **✅ Stage Tree**: 23 DOF ArticulationRoot visible and functional
- **✅ Visual Rendering**: Robot appears correctly in viewport
- **✅ Collision**: Robot interacts properly with ground plane

### 🔧 **Technical Validation:**
- **Robot Model**: Unitree G1 23-DOF with static Inspire hands
- **Physics Response**: Natural gravity response, no explosions or instabilities
- **USD Structure**: ArticulationRoot with proper joint hierarchy
- **System**: Ubuntu 24.04 + RTX 4070 Super + Isaac Sim 5.0.0

### 🏆 **MILESTONE ACHIEVED:**
**G1 robot successfully converted URDF → USD and validated in Isaac Sim physics simulation!**

**Generated with [Claude Code](https://claude.ai/code) - STEP 3: G1 USD Smoke Test Guide**