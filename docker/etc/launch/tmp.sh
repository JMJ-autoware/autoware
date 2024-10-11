SCRIPT_DIR=$(readlink -f "$(dirname "$0")")
# source "$SCRIPT_DIR/install/setup.bash"
ros2 launch "$SCRIPT_DIR/launcher.launch.py" \
      config_launch:="autoware_launch planning_simulator.launch.xml" \
      target_launch:="autoware_launch components/tier4_simulator_component.launch.xml" \
      map_path:=/autoware_map \
      vehicle_model:=sample_vehicle \
      sensor_model:=sample_sensor_kit \
      rviz:=false \
      print_include_error:=true &
ros2 launch "$SCRIPT_DIR/launcher.launch.py" \
      config_launch:="autoware_launch planning_simulator.launch.xml" \
      target_launch:="autoware_launch autoware.launch.xml" \
      map_path:=/autoware_map \
      vehicle_model:=sample_vehicle \
      sensor_model:=sample_sensor_kit \
      rviz:=false \
      print_include_error:=true
