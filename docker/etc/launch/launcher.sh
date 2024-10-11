SCRIPT_DIR=$(readlink -f "$(dirname "$0")")
# source "$SCRIPT_DIR/install/local_setup.bash"
ros2 launch "$SCRIPT_DIR/launcher.launch.py" "$@"
