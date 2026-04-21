# Copyright 2024 LIMO Workshop
# SPDX-License-Identifier: Apache-2.0
#
# Launch File: navigation_astar.launch.py
#
# Purpose: Start Nav2 autonomous navigation using the A* global planner
# (nav2_smac_planner/SmacPlanner2d) for the LIMO robot.
# This assumes:
#   • Gazebo is already running (launched separately)
#   • A pre-built map YAML file is available
#
# Usage (default map supplied with the package):
#   ros2 launch limo_navigation navigation_astar.launch.py
#
# Usage with your freshly-saved SLAM map:
#   ros2 launch limo_navigation navigation_astar.launch.py \
#       map:=$HOME/maps/workshop_map.yaml
# ─────────────────────────────────────────────────────────────────────────────

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # ── Package directories ──────────────────────────────────────────────────
    pkg_nav2     = get_package_share_directory('nav2_bringup')
    pkg_workshop = get_package_share_directory('limo_navigation')

    # ── Launch arguments ─────────────────────────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock',
    )
    map_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_workshop, 'maps', 'simple_map.yaml'),
        description='Full path to the map YAML file',
    )
    params_arg = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_workshop, 'params', 'nav2_params_astar.yaml'),
        description='Full path to the Nav2 parameters file',
    )
    autostart_arg = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Auto-start Nav2 lifecycle nodes',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml     = LaunchConfiguration('map')
    params_file  = LaunchConfiguration('params_file')
    autostart    = LaunchConfiguration('autostart')

    # ── Nav2 bringup (localisation + planning + control) ─────────────────────
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time':  use_sim_time,
            'map':           map_yaml,
            'params_file':   params_file,
            'autostart':     autostart,
        }.items(),
    )

    # ── RViz2 with Nav2 default config ───────────────────────────────────────
    rviz_config = os.path.join(pkg_workshop, 'rviz', 'navigation.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        use_sim_time_arg,
        map_arg,
        params_arg,
        autostart_arg,
        nav2_launch,
        TimerAction(period=3.0, actions=[rviz_node]),
    ])
