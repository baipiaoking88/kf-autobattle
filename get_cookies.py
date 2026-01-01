import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin
import sys

class CookieGetter:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_login_page(self, login_url):
        """Fetch the login page to inspect form fields"""
        try:
            response = self.session.get(login_url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching login page: {e}")
            return None

    def extract_form_data(self, html_content):
        """Extract form fields from login page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        login_form = soup.find('form')  # Find the first form or you can be more specific

        if not login_form:
            print("No login form found on the page")
            return None

        form_data = {}
        inputs = login_form.find_all('input')

        for input_tag in inputs:
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            input_type = input_tag.get('type', 'text')

            if name:
                # Only store hidden fields and other form values, not the username/password fields
                if input_type == 'hidden' or input_type == 'text' and name not in ['pwuser', 'pwpwd']:
                    form_data[name] = value
                elif input_type == 'submit':
                    # Include submit button if it has a value
                    if value:
                        form_data[name] = value

        return form_data

    def login(self, login_url, username, password):
        """Perform login with provided credentials"""
        # First, get the login page to extract any hidden form fields
        response = self.get_login_page(login_url)
        if not response:
            return False

        # Extract form data including hidden fields
        form_data = self.extract_form_data(response.text)
        if not form_data:
            print("Could not extract form data")
            return False

        # Update form data with actual credentials
        # Based on inspection, the fields are 'pwuser' for username and 'pwpwd' for password
        updated_form_data = form_data.copy()

        # Set the correct field names based on our inspection
        updated_form_data['pwuser'] = username
        updated_form_data['pwpwd'] = password

        # Perform the login request
        try:
            # Determine if we need to use the original URL or a form action URL
            login_action = login_url
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')
            if form and form.get('action'):
                login_action = urljoin(login_url, form['action'])

            login_response = self.session.post(login_action, data=updated_form_data)

            # Check if login was successful
            # This might need to be adjusted based on the actual site's response
            if login_response.status_code == 200:
                # Check if we're still on the login page or redirected to another page
                if 'login' not in login_response.url.lower():
                    print("Login successful!")
                    return True
                else:
                    # Check for success messages in the response even if still on login page
                    # (Some sites show success message and redirect via JavaScript/meta-refresh)
                    page_content = login_response.text
                    success_messages = ['顺利登录', '登录成功', '欢迎您', 'logout', 'welcome', 'dashboard', 'profile', username.lower()]
                    page_content_lower = page_content.lower()

                    if any(success_msg in page_content_lower for success_msg in success_messages):
                        print("Login successful!")
                        return True
                    else:
                        print("Login might have failed - still on login page")
                        # Print error message if available
                        if '错误' in page_content or 'error' in page_content_lower:
                            print("Error detected in response. Please check your credentials.")
                        return False
            else:
                print(f"Login request failed with status code: {login_response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error during login: {e}")
            return False

    def get_cookies(self):
        """Return the session cookies as a dictionary"""
        return self.session.cookies.get_dict()

    def save_cookies_to_file(self, filename='session_cookies.json'):
        """Save the session cookies to a file"""
        cookies = self.get_cookies()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"Cookies saved to {filename}")
        return cookies


def get_user_input_interactive():
    """Get user input in interactive mode"""
    try:
        import getpass

        print("=== Website Cookie Getter ===")
        print("This script will help you get login cookies for a website.")

        # Get website URL
        default_url = "https://bbs.kfpromax.com/login.php"
        url = input(f"Enter the login URL (press Enter for default: {default_url}): ").strip()
        if not url:
            url = default_url

        # Get username
        username = input("Enter your username: ").strip()

        # Get password securely
        password = getpass.getpass("Enter your password: ")

        return url, username, password
    except EOFError:
        print("Error: This script requires interactive input.")
        print("Please run this script directly in a terminal, not from an automated environment.")
        return None, None, None


def main():
    # Check if running in interactive mode
    if sys.stdin.isatty():
        url, username, password = get_user_input_interactive()
        if url is None:
            return None
    else:
        # Non-interactive mode - provide instructions
        print("=== Website Cookie Getter ===")
        print("This script helps you get login cookies for a website.")
        print("\nTo use this script, run it directly in a terminal:")
        print("  python3 get_cookies.py")
        print("\nIt will prompt you for:")
        print("  - Login URL (default: https://bbs.kfpromax.com/login.php)")
        print("  - Username")
        print("  - Password (entered securely, won't be displayed)")
        print("\nThe script will then log in and save the session cookies to a file.")
        return None

    print("\nAttempting to log in...")

    # Create cookie getter instance
    cookie_getter = CookieGetter()

    # Attempt login
    login_success = cookie_getter.login(url, username, password)

    if login_success:
        print("\nSuccessfully logged in!")

        # Get and display cookies
        cookies = cookie_getter.get_cookies()
        print(f"\nRetrieved {len(cookies)} cookies:")
        for name, value in cookies.items():
            # Don't print sensitive values like passwords
            if 'pwd' in name.lower() or 'password' in name.lower() or 'pass' in name.lower():
                print(f"  {name}: [HIDDEN]")
            else:
                print(f"  {name}: {value}")

        # Ask if user wants to save cookies to file
        try:
            save_choice = input("\nDo you want to save cookies to a file? (y/n): ").strip().lower()
            if save_choice in ['y', 'yes']:
                filename = input("Enter filename to save cookies (press Enter for 'session_cookies.json'): ").strip()
                if not filename:
                    filename = 'session_cookies.json'
                cookie_getter.save_cookies_to_file(filename)
        except EOFError:
            print("\nSkipping file save in non-interactive mode.")

        return cookies
    else:
        print("\nFailed to log in. Please check your credentials and try again.")
        return None


if __name__ == "__main__":
    cookies = main()
    if cookies:
        print("\nCookie retrieval completed successfully!")
    else:
        print("\nCookie retrieval failed or was cancelled.")