import ntplib
import time
import logging

def synchronize_time(ntp_server='pool.ntp.org', max_retries=3, backoff_factor=1):
    """
    Synchronize local time with an NTP server.

    Args:
        ntp_server (str): The NTP server to synchronize with. Default is 'pool.ntp.org'.
        max_retries (int): The maximum number of retry attempts. Default is 3.
        backoff_factor (int): The exponential backoff factor for retrying. Default is 1.

    Returns:
        float: The time offset in seconds if synchronization is successful, otherwise 0.

    """
    client = ntplib.NTPClient()
    retries = 0
    while retries < max_retries:
        try:
            response = client.request(ntp_server)
            offset = response.offset
            logging.info("Time synchronized with %s. Offset: %s seconds", ntp_server, offset)
            return offset
        except ntplib.NTPException as e:
            logging.warning("Failed to synchronize time on attempt %s with %s: %s", retries + 1, ntp_server, e)
            retries += 1
            time.sleep(backoff_factor * retries)  # Exponential backoff
        except Exception as e:
            logging.error("An error occurred during time synchronization: %s", e)
            return 0
    logging.error("Max retries (%s) reached. Unable to synchronize time with %s.", max_retries, ntp_server)
    return 0  # Return 0 offset if synchronization fails

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    offset = synchronize_time()
    print("Time offset:", offset, "seconds")
