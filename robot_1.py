import logging
import threading
from queue import Queue
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Robot:
    def __init__(self, robot_id):
        self.id = robot_id
        self.account = None
        self.status = "Idle"
        self.task_queue = Queue()
        self.activities = []
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        logging.info(f"Robot {self.id} initialized and thread started.")

    def create_account(self, account_info):
        if not account_info:
            logging.error(f"Account information for Robot {self.id} is empty.")
            return
        self.account = account_info
        logging.info(f"Account created for Robot {self.id}: {self.account}")

    def perform_activity(self, activity):
        if not self.account:
            logging.warning(f"Robot {self.id} does not have an account. Cannot perform activity.")
            return
        if not activity:
            logging.error(f"Activity for Robot {self.id} is not specified.")
            return
        self.task_queue.put(activity)
        logging.info(f"Activity '{activity}' assigned to Robot {self.id}.")

    def run(self):
        while True:
            activity = self.task_queue.get()
            if activity:
                self.status = "Working"
                logging.info(f"Robot {self.id} started performing activity: {activity}")
                try:
                    # Fetching data from an API using httpx
                    response = httpx.get(activity)
                    response.raise_for_status()  # Check response status
                    data = response.json()
                    logging.info(f"Robot {self.id} fetched data: {data}")
                    self.activities.append(activity)  # Store activity
                except httpx.HTTPStatusError as e:
                    logging.error(f"Robot {self.id} failed to fetch data. Status code: {e.response.status_code}")
                except Exception as e:
                    logging.error(f"Robot {self.id} encountered an unexpected error: {e}")
                self.status = "Idle"
                logging.info(f"Robot {self.id} completed activity: {activity}")
            self.task_queue.task_done()

class RobotManager:
    def __init__(self):
        self.robots = {}
        self.lock = threading.Lock()

    def add_robot(self, account_info=None):
        with self.lock:
            new_id = len(self.robots) + 1
            robot = Robot(new_id)
            self.robots[new_id] = robot
            logging.info(f"Robot {new_id} has been added.")
            if account_info:
                robot.create_account(account_info)
            return new_id

    def remove_robot(self, robot_id):
        with self.lock:
            robot = self.robots.pop(robot_id, None)
            if robot:
                logging.info(f"Robot {robot_id} has been removed.")
                return True
            else:
                logging.warning(f"Robot {robot_id} was not found.")
                return False

    def create_accounts(self, account_info_list):
        with self.lock:
            if len(account_info_list) != len(self.robots):
                logging.error("The number of account informations does not match the number of robots.")
                raise ValueError("The length of account_info_list must be equal to the number of robots.")
            for robot, account_info in zip(self.robots.values(), account_info_list):
                robot.create_account(account_info)

    def execute_activities(self, activities):
        with self.lock:
            if len(activities) != len(self.robots):
                logging.error("The number of activities does not match the number of robots.")
                raise ValueError("The length of activities must be equal to the number of robots.")
            for robot, activity in zip(self.robots.values(), activities):
                robot.perform_activity(activity)

    def assign_task_to_robot(self, robot_id, activity):
        with self.lock:
            robot = self.robots.get(robot_id)
            if robot:
                robot.perform_activity(activity)
                return True
            else:
                logging.warning(f"Robot {robot_id} was not found.")
                return False

    def list_robots(self):
        with self.lock:
            robot_list = []
            for robot in self.robots.values():
                robot_info = {
                    "id": robot.id,
                    "account": robot.account,
                    "status": robot.status,
                    "activities": robot.activities
                }
                robot_list.append(robot_info)
            return robot_list

    def get_robot_status(self, robot_id):
        with self.lock:
            robot = self.robots.get(robot_id)
            if robot:
                return {
                    "id": robot.id,
                    "account": robot.account,
                    "status": robot.status,
                    "activities": robot.activities
                }
            else:
                return None

def display_menu():
    menu = """
    ===== Robot Management Menu =====
    1. List all robots
    2. Add a new robot
    3. Remove a robot
    4. Create accounts for robots
    5. Execute activities for robots
    6. Assign task to a specific robot
    7. Get status of a specific robot
    8. Exit
    ===================================
    Please enter your choice: """
    return input(menu)

def main():
    manager = RobotManager()

    try:
        initial_robot_count = int(input("Enter the initial number of robots: "))
        for _ in range(initial_robot_count):
            manager.add_robot()
        print(f"{initial_robot_count} robots have been added.")

        while True:
            choice = display_menu()

            if choice == '1':
                robots = manager.list_robots()
                if not robots:
                    print("No robots available.")
                else:
                    print("List of Robots:")
                    for robot in robots:
                        account_status = robot['account'] if robot['account'] else "No Account"
                        print(f"Robot {robot['id']}: {account_status}, Status: {robot['status']}, Activities: {robot['activities']}")

            elif choice == '2':
                account_info = input("Enter account name for the new robot (leave empty if none): ")
                robot_id = manager.add_robot(account_info if account_info else None)
                print(f"New robot with ID {robot_id} has been added.")

            elif choice == '3':
                try:
                    robot_id = int(input("Enter the ID of the robot you want to remove: "))
                    success = manager.remove_robot(robot_id)
                    if success:
                        print(f"Robot {robot_id} has been removed.")
                    else:
                        print(f"Robot {robot_id} was not found.")
                except ValueError:
                    print("Invalid input. Please enter a numeric robot ID.")

            elif choice == '4':
                print("Please enter account information for each robot:")
                accounts = []
                for robot in manager.list_robots():
                    account = input(f"Account for Robot {robot['id']}: ")
                    accounts.append(account)
                try:
                    manager.create_accounts(accounts)
                    print("Accounts have been created for all robots.")
                except ValueError as ve:
                    print(f"Error: {ve}")

            elif choice == '5':
                print("Please enter activities for each robot:")
                activities = []
                for robot in manager.list_robots():
                    activity = input(f"Activity for Robot {robot['id']} (Enter a valid API URL): ")
                    activities.append(activity)
                try:
                    manager.execute_activities(activities)
                    print("Activities have been assigned to all robots.")
                except ValueError as ve:
                    print(f"Error: {ve}")

            elif choice == '6':
                try:
                    robot_id = int(input("Enter the ID of the robot you want to assign a task to: "))
                    activity = input("Enter the activity (API URL) for the robot: ")
                    if not activity:
                        print("No activity specified.")
                    else:
                        success = manager.assign_task_to_robot(robot_id, activity)
                        if success:
                            print(f"Task '{activity}' has been assigned to Robot {robot_id}.")
                        else:
                            print(f"Robot {robot_id} was not found.")
                except ValueError:
                    print("Invalid input. Please enter a numeric robot ID.")

            elif choice == '7':
                try:
                    robot_id = int(input("Enter the ID of the robot you want to check status for: "))
                    status = manager.get_robot_status(robot_id)
                    if status:
                        account_status = status['account'] if status['account'] else "No Account"
                        print(f"Robot {status['id']}: {account_status}, Status: {status['status']}, Activities: {status['activities']}")
                    else:
                        print(f"Robot {robot_id} was not found.")
                except ValueError:
                    print("Invalid input. Please enter a numeric robot ID.")

            elif choice == '8':
                print("Exiting the program.")
                break

            else:
                print("Invalid option. Please try again.")

    except Exception as e:
        logging.exception("An error occurred:")

if __name__ == "__main__":
    main()
