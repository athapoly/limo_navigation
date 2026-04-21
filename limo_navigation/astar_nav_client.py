# Copyright 2024 LIMO Workshop
# SPDX-License-Identifier: Apache-2.0
"""
astar_nav_client.py
───────────────────
A ROS 2 action client that sends a single navigation goal to Nav2's
NavigateToPose action server (which uses the A* SmacPlanner2d under the hood).

Run after launching Gazebo + navigation_astar.launch.py:

    ros2 run limo_navigation astar_nav_client -- --x 2.0 --y 1.0 --yaw 0.0

The script will:
  1. Connect to the /navigate_to_pose action server
  2. Send the goal pose
  3. Stream feedback (estimated time remaining, distance to goal)
  4. Report success or failure
"""

import argparse
import math
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose


def yaw_to_quaternion(yaw: float) -> Quaternion:
    """Convert a yaw angle (radians) to a geometry_msgs/Quaternion."""
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class AStarNavClient(Node):
    """Sends one NavigateToPose goal and waits for the result."""

    def __init__(self, x: float, y: float, yaw: float):
        super().__init__('astar_nav_client')
        self._x   = x
        self._y   = y
        self._yaw = yaw
        self._done = False

        self._client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    # ── Public API ─────────────────────────────────────────────────────────
    def send_goal(self) -> None:
        self.get_logger().info('Waiting for NavigateToPose action server…')
        self._client.wait_for_server()

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp    = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = self._x
        goal_msg.pose.pose.position.y = self._y
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation = yaw_to_quaternion(self._yaw)

        self.get_logger().info(
            f'Sending goal → x={self._x:.2f}  y={self._y:.2f}'
            f'  yaw={math.degrees(self._yaw):.1f}°'
        )

        self._send_goal_future = self._client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_cb,
        )
        self._send_goal_future.add_done_callback(self._goal_response_cb)

    def is_done(self) -> bool:
        return self._done

    # ── Callbacks ──────────────────────────────────────────────────────────
    def _goal_response_cb(self, future) -> None:
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal was REJECTED by the action server.')
            self._done = True
            return
        self.get_logger().info('Goal ACCEPTED – robot is navigating…')
        self._result_future = goal_handle.get_result_async()
        self._result_future.add_done_callback(self._result_cb)

    def _feedback_cb(self, feedback_msg) -> None:
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'  Distance remaining: {fb.distance_remaining:.2f} m'
        )

    def _result_cb(self, future) -> None:
        result = future.result()
        status = result.status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('✔  Navigation SUCCEEDED!')
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn('Navigation was CANCELLED.')
        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error('Navigation was ABORTED (obstacle / timeout?).')
        else:
            self.get_logger().warn(f'Navigation finished with status: {status}')
        self._done = True


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Send a single Nav2 A* goal to the LIMO robot.'
    )
    parser.add_argument('--x',   type=float, default=2.0,
                        help='Goal X coordinate in the map frame (metres)')
    parser.add_argument('--y',   type=float, default=0.0,
                        help='Goal Y coordinate in the map frame (metres)')
    parser.add_argument('--yaw', type=float, default=0.0,
                        help='Goal heading in radians (default 0 = East)')
    # argparse + ros2 run passes ROS args after --, filter them out
    filtered = [a for a in argv if not a.startswith('__')]
    return parser.parse_args(filtered)


def main(args=None):
    rclpy.init(args=args)
    # sys.argv[1:] to allow ros2 run -- --x ... forwarding
    parsed = parse_args(sys.argv[1:])

    node = AStarNavClient(x=parsed.x, y=parsed.y, yaw=parsed.yaw)
    node.send_goal()

    try:
        while rclpy.ok() and not node.is_done():
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
