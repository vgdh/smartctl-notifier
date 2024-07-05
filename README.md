# Smartctl Notifier

This tool helps you monitor your HDD or NVMe disk for changes in SMART values, indicating potential failures and notify you some when a failure values changed. It also sends a daily "I am alive" message to confirm that the tool is active.

## How to Use

1. Clone the repository:
    ```bash
    cd /root/
    git clone https://github.com/vgdh/smartctl-notifier
    ```

2. Run the app once to create the necessary file structure:
    ```bash
    cd /root/smartctl-notifier/ && python3 smartctl-notifier.py
    ```

3. Open the email configuration file and add your email credentials:
    ```bash
    nano /root/smartctl-notifier/.smartctl-notifier-storage/email_credential
    ```
    Add your credentials to the file:
    ```
    yourmail@yourprovider.com
    youraccesstoken_or_password
    ```

4. Run the app again to ensure there are no errors in the console log:
    ```bash
    cd /root/smartctl-notifier/ && python3 smartctl-notifier.py
    ```

5. Set up a cron task to run the app hourly:
    ```bash
    0 * * * * cd /root/smartctl-notifier/ && python3 smartctl-notifier.py
    ```

---

This version addresses grammatical issues, corrects typos (e.g., "notifyer" to "notifier"), and improves the overall flow and readability.
