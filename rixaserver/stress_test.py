import asyncio
import json
import time
import aiohttp
import random
import logging
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stress_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("stress_test")

# Shared data structure to track all messages across users
all_message_responses = {}
message_sequence = []  # To track message order for plotting
user_fetch_files = []  # To track fetch times for each user
user_total_fetch_times = []  # To track total fetch times for all users

class ChatbotStressTest:
    def __init__(self, base_url="https://rixa.ai", username="test_user", password="test_password", use_ws=False,
                 msg_file_path=None, max_msgs=10, reload_times = 1):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.ws_url = None  # Will be determined later
        self.session = None
        self.ws = None
        self.csrf_token = None
        self.connected = False
        self.use_ws = use_ws
        self.last_msg_id = -2
        self.msg_file_path = msg_file_path
        self.message_counter = 0  # Track the message number for this user
        self.total_fetch_time = 0  # Total time taken to fetch static files
        self.total_fetched_files = 0  # Total number of static files fetched
        self.max_msgs = max_msgs
        self.reload_times = reload_times

    async def start(self):
        """Initialize the session and run the stress test"""
        self.session = aiohttp.ClientSession()
        try:
            # Login and navigate to dashboard
            for i in range(self.reload_times):
                await self.login()
                await self.load_dashboard()

            # Connect to WebSocket
            await self.connect_websocket()

            # Send test messages
            await self.send_test_messages()

        except Exception as e:
            logger.error(f"Error during stress test for {self.username}: {str(e)}", exc_info=True)
        finally:
            await self.cleanup()

    async def login(self):
        """Fetch login page, extract CSRF token, and login"""
        login_url = urljoin(self.base_url, "/de/account_management/user_login_old/")
        logger.info(f"{self.username}: Fetching login page: {login_url}")

        # Get login page and CSRF token
        start_time = time.time()
        async with self.session.get(login_url) as response:
            html = await response.text()
            elapsed = time.time() - start_time
            logger.info(f"{self.username}: Login page loaded in {elapsed:.2f} seconds")

            # Parse the page to get the CSRF token
            soup = BeautifulSoup(html, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if not csrf_input:
                raise ValueError(f"{self.username}: Could not find CSRF token in login page")

            self.csrf_token = csrf_input.get('value')
            logger.info(f"{self.username}: CSRF token extracted: {self.csrf_token[:5]}...")

            # Fetch static files from login page
            await self.fetch_static_files(soup, login_url)

        # Perform login
        login_data = {
            'csrfmiddlewaretoken': self.csrf_token,
            'username': self.username,
            'password': self.password,
        }

        headers = {
            'Referer': login_url,
        }

        logger.info(f"{self.username}: Attempting to login")
        start_time = time.time()
        cookies = {'csrftoken': self.csrf_token}
        async with self.session.post(login_url, data=login_data, headers=headers, allow_redirects=True,
                                     cookies=cookies) as response:
            elapsed = time.time() - start_time
            logger.info(
                f"{self.username}: Login request completed in {elapsed:.2f} seconds with status {response.status}")

            if response.status != 200:
                logger.error(f"{self.username}: Login failed with status code {response.status}")
                raise ValueError(f"Login failed with status code {response.status}")

            # Check if login was successful by looking for specific elements or redirect
            html = await response.text()
            if "Invalid username or password" in html:
                logger.error(f"{self.username}: Login failed: Invalid username or password")
                raise ValueError("Login failed: Invalid username or password")

            logger.info(f"{self.username}: Login successful")

    async def load_dashboard(self):
        """Load the dashboard page and extract WebSocket URL"""
        dashboard_url = urljoin(self.base_url, "/de/dashboard/home")
        logger.info(f"{self.username}: Navigating to dashboard: {dashboard_url}")

        start_time = time.time()
        async with self.session.get(dashboard_url) as response:
            elapsed = time.time() - start_time
            logger.info(f"{self.username}: Dashboard loaded in {elapsed:.2f} seconds with status {response.status}")

            if response.status != 200:
                logger.error(f"{self.username}: Failed to load dashboard with status code {response.status}")
                raise ValueError(f"Failed to load dashboard with status code {response.status}")

            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            # Fetch static files from dashboard page
            await self.fetch_static_files(soup, dashboard_url)

            if self.use_ws:
                ws_url = f"ws://{self.base_url.split('//')[1]}/ws/chat/"
            else:
                ws_url = f"wss://{self.base_url.split('//')[1]}/ws/chat/"
            self.ws_url = ws_url

    async def fetch_static_files(self, soup, page_url):
        """Fetch static files (CSS, JS, images) from a page to simulate browser behavior"""
        static_files = []

        # Find all CSS files
        for css in soup.find_all('link', rel='stylesheet'):
            if css.get('href'):
                static_files.append(('CSS', css.get('href')))

        # Find all JavaScript files
        for script in soup.find_all('script'):
            if script.get('src'):
                static_files.append(('JS', script.get('src')))

        # Find all images
        for img in soup.find_all('img'):
            if img.get('src'):
                static_files.append(('IMG', img.get('src')))

        # Find all favicon links
        for favicon in soup.find_all('link', rel='icon'):
            if favicon.get('href'):
                static_files.append(('ICO', favicon.get('href')))

        # logger.info(f"{self.username}: Found {len(static_files)} static files to fetch")

        tasks = []
        for file_type, file_path in static_files:
            # Convert relative URLs to absolute
            file_url = urljoin(page_url, file_path)
            tasks.append(self.fetch_single_static(file_type, file_url))

        # Execute all fetch tasks concurrently with a limit
        max_concurrent = min(10, len(tasks))  # Limit concurrent requests

        if tasks:
            start_time = time.time()
            # Use gather with semaphore to limit concurrency
            sem = asyncio.Semaphore(max_concurrent)

            async def fetch_with_semaphore(task):
                async with sem:
                    return await task

            await asyncio.gather(*(fetch_with_semaphore(task) for task in tasks))
            elapsed = time.time() - start_time
            logger.info(f"{self.username}: Fetched {len(tasks)} static files in {elapsed:.2f} seconds")
            self.total_fetch_time += elapsed
            self.total_fetched_files += len(tasks)
            user_fetch_files.append(len(tasks))
            user_total_fetch_times.append(elapsed)

    async def fetch_single_static(self, file_type, url):
        """Fetch a single static file and log result"""
        try:
            start_time = time.time()
            async with self.session.get(url, timeout=5) as response:
                # Just read the response to complete the request
                _ = await response.read()
                elapsed = time.time() - start_time
                if response.status == 200:
                    logger.debug(f"{self.username}: Fetched {file_type} {url} in {elapsed:.2f}s")
                else:
                    logger.warning(f"{self.username}: Failed to fetch {file_type} {url}: {response.status}")
                return elapsed, response.status
        except Exception as e:
            logger.warning(f"{self.username}: Error fetching {file_type} {url}: {str(e)}")
            return None, None

    async def connect_websocket(self):
        """Establish WebSocket connection"""
        logger.info(f"{self.username}: Connecting to WebSocket: {self.ws_url}")

        try:
            start_time = time.time()
            self.ws = await self.session.ws_connect(self.ws_url)
            elapsed = time.time() - start_time
            logger.info(f"{self.username}: WebSocket connection established in {elapsed:.2f} seconds")

            # Start listening for messages
            asyncio.create_task(self.listen_for_messages())
            self.connected = True

        except Exception as e:
            logger.error(f"{self.username}: Failed to connect to WebSocket: {str(e)}", exc_info=True)
            raise

    async def listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        logger.info(f"{self.username}: Started listening for WebSocket messages")

        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"{self.username}: WebSocket connection closed with error: {self.ws.exception()}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info(f"{self.username}: WebSocket connection closed")
                    break
        except Exception as e:
            logger.error(f"{self.username}: Error in WebSocket message listener: {str(e)}", exc_info=True)
        finally:
            self.connected = False
            logger.info(f"{self.username}: Stopped listening for WebSocket messages")

    async def handle_message(self, data):
        """Process incoming WebSocket messages"""
        try:
            message = json.loads(data)
            msg_type = message.get("role")

            if msg_type == "tracker_entry":
                msg_id = self.last_msg_id

                # Get the global response record for this message
                global_msg_id = f"{self.username}_{msg_id}"
                if global_msg_id in all_message_responses:
                    start_time = all_message_responses[global_msg_id]["start_time"]
                    elapsed = time.time() - start_time
                    content = message["tracker"]["content"].replace('\n', '')
                    msg_length = len(content)
                    metadata = message["tracker"]["metadata"]
                    tokens = metadata.get("total_tokens", 0)
                    used_citations = len(metadata.get("used_citations", []))

                    logger.info(
                        f"{self.username}: Message {msg_id} with {tokens} tokens and {used_citations} citations received complete response in {elapsed:.2f} seconds, '{content[:50]}...'")

                    # Update the shared data structure
                    all_message_responses[global_msg_id].update({
                        "elapsed": elapsed,
                        "completed": True,
                        "tokens": tokens,
                        "citations": used_citations,
                        "response_length": msg_length
                    })
            else:
                logger.debug(f"{self.username}: Received message of type: {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"{self.username}: Failed to parse WebSocket message: {data[:100]}...")
        except Exception as e:
            logger.error(f"{self.username}: Error handling WebSocket message: {str(e)}", exc_info=True)

    async def send_message(self, content):
        """Send a message over the WebSocket connection"""
        if not self.connected:
            logger.error(f"{self.username}: Cannot send message: WebSocket not connected")
            return None

        self.last_msg_id += 2
        msg_id = self.last_msg_id
        self.message_counter += 1

        message = {'type': 'usr_msg', 'content': content, 'index': self.last_msg_id, 'role': 'user'}

        # Create a unique global message ID
        global_msg_id = f"{self.username}_{msg_id}"

        # Record the start time in the shared data structure
        all_message_responses[global_msg_id] = {
            "username": self.username,
            "content": content,
            "start_time": time.time(),
            "completed": False,
            "message_number": self.message_counter,
            "content_length": len(content)
        }

        # Add to sequence for plotting
        message_sequence.append({
            "global_msg_id": global_msg_id,
            "message_number": self.message_counter,
            "timestamp": time.time()
        })

        await self.ws.send_str(json.dumps(message))

        return global_msg_id

    async def send_test_messages(self):
        """Send a series of test messages and record response times"""
        default_path = __file__.replace("stress_test.py", "stress_test_messages.txt")
        if self.msg_file_path:
            default_path = self.msg_file_path

        with open(default_path) as f:
            test_messages = f.readlines()[:self.max_msgs]

        # Send messages with random delays between them
        for i, message in enumerate(test_messages):
            if not self.connected:
                logger.error(f"{self.username}: WebSocket disconnected, stopping test")
                break

            logger.info(f"{self.username}: Sending test message {i + 1}/{len(test_messages)}, '{message[:50].strip()}'")
            global_msg_id = await self.send_message(message)

            # Wait for the response to complete or timeout
            timeout = 30  # seconds
            start_wait = time.time()
            while global_msg_id in all_message_responses and not all_message_responses[global_msg_id]["completed"]:
                if time.time() - start_wait > timeout:
                    logger.warning(f"{self.username}: Timeout waiting for response to message {global_msg_id}")
                    break
                await asyncio.sleep(0.5)

            # Random delay between messages
            delay = random.uniform(1, 3)
            logger.info(f"{self.username}: Waiting {delay:.2f} seconds before next message")
            await asyncio.sleep(delay)

    async def cleanup(self):
        """Close WebSocket connection and session"""
        logger.info(f"{self.username}: Cleaning up resources")

        if self.ws and not self.ws.closed:
            await self.ws.close()
            logger.info(f"{self.username}: WebSocket connection closed")

        if self.session:
            await self.session.close()
            logger.info(f"{self.username}: HTTP session closed")


async def run_stress_test(username, password, base_url="https://rixa.ai", concurrent_users=1, use_ws=False,
                          msg_file_path=None, max_msgs=10, reload_times=1):
    """Run multiple concurrent stress tests"""
    logger.info(f"Starting stress test with {concurrent_users} concurrent users")
    tasks = []

    for i in range(concurrent_users):
        user_id = f"{username}_{i + 1}"
        test = ChatbotStressTest(base_url=base_url, username=user_id, password=password, use_ws=use_ws,
                                 msg_file_path=msg_file_path, max_msgs=max_msgs, reload_times=reload_times)
        tasks.append(test.start())

    await asyncio.gather(*tasks)
    logger.info("All stress tests completed")

    # Generate the combined report and plots
    await generate_combined_report(concurrent_users)


async def generate_combined_report(num_users):
    """Generate a combined report of message response times for all users"""
    logger.info("Generating combined stress test report")

    total_messages = len(all_message_responses)
    completed_messages = sum(1 for data in all_message_responses.values() if data.get("completed", False))

    if total_messages == 0:
        logger.warning("No messages were sent during the test")
    else:
        completion_rate = (completed_messages / total_messages) * 100

        # Calculate response time statistics
        response_times = [data.get("elapsed", float("inf")) for data in all_message_responses.values()
                          if data.get("completed", False) and "elapsed" in data]

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            median_response_time = sorted(response_times)[len(response_times) // 2]
        else:
            avg_response_time = min_response_time = max_response_time = median_response_time = float("inf")

    # Fetch static files statistics
    total_fetch_time = sum(user_total_fetch_times)
    total_fetched_files = sum(user_fetch_files)
    avg_fetch_time = total_fetch_time / total_fetched_files if total_fetched_files > 0 else 0

    # Group by user
    user_stats = defaultdict(list)
    for msg_id, data in all_message_responses.items():
        if data.get("completed", False) and "elapsed" in data:
            username = data.get("username")
            user_stats[username].append(data.get("elapsed"))

    # Generate the report
    report = f"""
    ===== CHATBOT STRESS TEST COMBINED REPORT =====
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    if total_messages>0:
        report += f"""
    TEST SUMMARY:
    - Number of users: {num_users}
    - Total messages sent: {total_messages}
    - Received answer rate: {completion_rate:.2f}%

    RESPONSE TIME METRICS:
    - Average response time: {avg_response_time:.2f} seconds
    - Median response time: {median_response_time:.2f} seconds
    - Minimum response time: {min_response_time:.2f} seconds
    - Maximum response time: {max_response_time:.2f} seconds"""
    report+=f"""
    STATIC FILES FETCHED:
    - Total fetch time: {total_fetch_time:.2f} seconds
    - Total fetched files: {total_fetched_files}
    - Average fetch time: {avg_fetch_time:.2f} seconds per file
    - Total fetch time per user: {total_fetch_time / num_users:.2f} seconds
    """

    # Add per-user statistics
    # report += "\nPER-USER STATISTICS:\n"
    # for username, times in user_stats.items():
    #     avg_time = sum(times) / len(times)
    #     report += f"- {username}: {len(times)} messages, avg response time: {avg_time:.2f} seconds\n"

    report += "==============================================="

    # Log and save the report
    logger.info(report)
    with open("combined_stress_test_report.txt", "w") as f:
        f.write(report)

    logger.info("Combined stress test report saved to combined_stress_test_report.txt")

    # Generate plots
    await generate_plots()


async def generate_plots():
    # 1. Histogram of response times
    if all_message_responses:
        response_times = [data.get("elapsed") for data in all_message_responses.values()
                          if data.get("completed", False) and "elapsed" in data]

        plt.figure(figsize=(10, 6))
        plt.hist(response_times, bins=20, alpha=0.7, color='blue')
        plt.xlabel('Response Time (seconds)')
        plt.ylabel('Frequency')
        plt.title('Histogram of Response Times')
        plt.grid(True, alpha=0.3)
        plt.savefig('response_time_histogram.png')
        plt.close()

        # 2. Response time over messages
        # Sort message data by sequence
        message_data = []
        for msg_id, data in all_message_responses.items():
            if data.get("completed", False) and "elapsed" in data:
                message_data.append({
                    "username": data.get("username"),
                    "message_number": data.get("message_number"),
                    "elapsed": data.get("elapsed")
                })

        # Sort by message number
        message_data.sort(key=lambda x: x["message_number"])

        # Prepare data for plotting
        usernames = set(item["username"] for item in message_data)

        plt.figure(figsize=(12, 7))

        for username in usernames:
            user_data = [item for item in message_data if item["username"] == username]
            message_numbers = [item["message_number"] for item in user_data]
            times = [item["elapsed"] for item in user_data]
            plt.scatter(message_numbers, times, alpha=0.7, label=username)

        plt.xlabel('Message Sequence Number')
        plt.ylabel('Response Time (seconds)')
        plt.title('Response Time vs Message Sequence')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('response_time_vs_message.png')
        plt.close()

        # Additional plot: Rolling average response time to show trends
        plt.figure(figsize=(12, 7))

        # Sort all data by timestamp for chronological view
        all_data = sorted(
            [item for item in message_data if "elapsed" in item],
            key=lambda x: x["message_number"]
        )

        message_nums = [item["message_number"] for item in all_data]
        response_times = [item["elapsed"] for item in all_data]

        # Plot individual points
        plt.scatter(message_nums, response_times, alpha=0.4, color='gray', label='Individual responses')

        # Calculate rolling average if we have enough data
        if len(response_times) > 5:
            window = min(5, len(response_times) // 3)
            rolling_avg = np.convolve(response_times, np.ones(window) / window, mode='valid')
            plt.plot(message_nums[window - 1:], rolling_avg, 'r-', linewidth=2, label=f'{window}-message rolling average')

        plt.xlabel('Message Sequence Number')
        plt.ylabel('Response Time (seconds)')
        plt.title('Response Time Trend')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('response_time_trend.png')
        plt.close()

    # histogram static files
    plt.figure(figsize=(10, 6))
    plt.hist(user_total_fetch_times, alpha=0.7, color='green')
    plt.xlabel('Fetch Time (seconds)')
    plt.ylabel('Frequency')
    plt.title('Histogram of Fetch Times per User')
    plt.grid(True, alpha=0.3)
    plt.savefig('fetch_time_histogram.png')

    logger.info("Generated plots")


def run():
    import argparse

    parser = argparse.ArgumentParser(description="Run a stress test on a chatbot interface")
    parser.add_argument("--username", required=True, help="Base username for the test")
    parser.add_argument("--password", required=True, help="Password for the test accounts")
    parser.add_argument("--base-url", default="https://rixa.ai", help="Base URL of the site")
    parser.add_argument("--users", type=int, default=1, help="Number of concurrent users to simulate")
    parser.add_argument("--use-ws", help="Use ws instead of wss", action="store_true")
    parser.add_argument("--msg_file_path", default=None, help="Path to the file containing messages to send")
    parser.add_argument("--max-msgs", type=int, default=10, help="Maximum number of messages to send")
    parser.add_argument("--reload-times", type=int, default=1, help="Number of times to reload the page")

    args = parser.parse_args()

    asyncio.run(run_stress_test(
        username=args.username,
        password=args.password,
        base_url=args.base_url,
        concurrent_users=args.users,
        use_ws=args.use_ws,
        msg_file_path=args.msg_file_path,
        max_msgs=args.max_msgs,
        reload_times=args.reload_times
    ))